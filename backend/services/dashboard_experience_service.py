from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.core.telemetry import log_timed_event, now_ms
from backend.models.student import StudentProfile, StudentSubject
from backend.models.subject import Subject
from backend.schemas.dashboard_schema import DashboardBootstrapOut
from backend.services.course_experience_service import CourseExperienceService
from backend.services.prewarm_job_service import PrewarmJobService

logger = logging.getLogger(__name__)
DASHBOARD_CACHE_TTL_SECONDS = 30.0
_DASHBOARD_BOOTSTRAP_CACHE: dict[str, tuple[float, DashboardBootstrapOut]] = {}


class DashboardExperienceError(ValueError):
    pass


class DashboardExperienceService:
    def __init__(self, db: Session):
        self.db = db
        self.course_service = CourseExperienceService(db)

    @staticmethod
    def _profile_signature(*, profile: StudentProfile, subjects: list[str]) -> str:
        payload = {
            "updated_at": profile.updated_at.isoformat() if getattr(profile, "updated_at", None) else "",
            "sss_level": str(profile.sss_level),
            "term": int(profile.active_term),
            "subjects": sorted(subjects),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _cache_key(*, student_id: UUID, subject: str | None, profile_signature: str) -> str:
        return ":".join([str(student_id), subject or "auto", profile_signature])

    @staticmethod
    def _read_cached_bootstrap(*, cache_key: str) -> DashboardBootstrapOut | None:
        entry = _DASHBOARD_BOOTSTRAP_CACHE.get(cache_key)
        if entry is None:
            return None
        created_at, payload = entry
        if (time.time() - created_at) > DASHBOARD_CACHE_TTL_SECONDS:
            _DASHBOARD_BOOTSTRAP_CACHE.pop(cache_key, None)
            return None
        return payload

    @staticmethod
    def _write_cached_bootstrap(*, cache_key: str, payload: DashboardBootstrapOut) -> DashboardBootstrapOut:
        _DASHBOARD_BOOTSTRAP_CACHE[cache_key] = (time.time(), payload)
        return payload

    @classmethod
    def invalidate_student_cache(cls, *, student_id: UUID) -> None:
        prefix = f"{student_id}:"
        for cache_key in [key for key in list(_DASHBOARD_BOOTSTRAP_CACHE.keys()) if key.startswith(prefix)]:
            _DASHBOARD_BOOTSTRAP_CACHE.pop(cache_key, None)

    @classmethod
    def cache_snapshot(cls) -> dict:
        cls._prune_cache()
        return {
            "status": "ok",
            "bootstrap_cache": {
                "entries": len(_DASHBOARD_BOOTSTRAP_CACHE),
                "ttl_seconds": DASHBOARD_CACHE_TTL_SECONDS,
            },
        }

    @classmethod
    def _prune_cache(cls) -> None:
        now = time.time()
        for cache_key, (created_at, _payload) in list(_DASHBOARD_BOOTSTRAP_CACHE.items()):
            if (now - created_at) > DASHBOARD_CACHE_TTL_SECONDS:
                _DASHBOARD_BOOTSTRAP_CACHE.pop(cache_key, None)

    @classmethod
    def prewarm(
        cls,
        *,
        student_id: UUID,
        subject: Literal["math", "english", "civic"] | None = None,
    ) -> bool:
        db = SessionLocal()
        try:
            cls(db).bootstrap(student_id=student_id, subject=subject)
            logger.info(
                "dashboard.bootstrap.prewarm_success student_id=%s subject=%s",
                student_id,
                subject or "auto",
            )
            return True
        except Exception as exc:  # pragma: no cover - best effort prewarm
            logger.warning(
                "dashboard.bootstrap.prewarm_failed student_id=%s subject=%s detail=%s",
                student_id,
                subject or "auto",
                exc,
            )
            return False
        finally:
            db.close()

    def _profile_and_subjects(
        self,
        *,
        student_id: UUID,
    ) -> tuple[StudentProfile, list[Literal["math", "english", "civic"]]]:
        profile = self.db.execute(
            select(StudentProfile).where(StudentProfile.student_id == student_id)
        ).scalar_one_or_none()
        if profile is None:
            raise DashboardExperienceError("Student profile not found.")

        rows = self.db.execute(
            select(Subject.slug)
            .join(StudentSubject, StudentSubject.subject_id == Subject.id)
            .where(StudentSubject.student_profile_id == profile.id)
            .order_by(Subject.slug.asc())
        ).all()
        subjects = [str(row[0]) for row in rows if str(row[0]) in {"math", "english", "civic"}]
        return profile, subjects  # type: ignore[return-value]

    def bootstrap(
        self,
        *,
        student_id: UUID,
        subject: Literal["math", "english", "civic"] | None = None,
    ) -> DashboardBootstrapOut:
        started_at = now_ms()
        profile, available_subjects = self._profile_and_subjects(student_id=student_id)
        profile_signature = self._profile_signature(profile=profile, subjects=available_subjects)
        cache_key = self._cache_key(
            student_id=student_id,
            subject=subject,
            profile_signature=profile_signature,
        )
        cached = self._read_cached_bootstrap(cache_key=cache_key)
        if cached is not None:
            log_timed_event(
                logger,
                "dashboard.bootstrap",
                started_at,
                cache_hit=True,
                student_id=student_id,
                requested_subject=subject or "auto",
                active_subject=cached.active_subject or "none",
                warmed_subjects=len(list(cached.warmed_subjects or [])),
            )
            return cached

        course_bootstrap = None
        active_subject = subject if subject in available_subjects else None
        course_bootstrap_source = "none"

        if active_subject is None:
            latest = self.course_service.latest_intervention_bootstrap(student_id=student_id)
            if latest is not None:
                course_bootstrap = latest
                active_subject = latest.subject
                course_bootstrap_source = "latest_intervention"

        if active_subject is None and available_subjects:
            active_subject = available_subjects[0]

        if active_subject is not None and course_bootstrap is None:
            course_bootstrap = self.course_service.bootstrap(
                student_id=student_id,
                subject=active_subject,
                term=int(profile.active_term),
            )
            course_bootstrap_source = "scope_bootstrap"

        warmed_subjects: list[Literal["math", "english", "civic"]] = []
        failed_subjects: list[Literal["math", "english", "civic"]] = []
        for candidate_subject in available_subjects:
            if candidate_subject == active_subject:
                continue
            if CourseExperienceService.prewarm_scope(
                student_id=student_id,
                subject=candidate_subject,
                term=int(profile.active_term),
            ):
                warmed_subjects.append(candidate_subject)
            else:
                failed_subjects.append(candidate_subject)
            PrewarmJobService(self.db).enqueue_course_scope(
                student_id=student_id,
                subject=candidate_subject,
                term=int(profile.active_term),
            )

        payload = DashboardBootstrapOut(
            student_id=student_id,
            sss_level=str(profile.sss_level),  # type: ignore[arg-type]
            term=int(profile.active_term),  # type: ignore[arg-type]
            available_subjects=available_subjects,
            active_subject=active_subject,
            warmed_subjects=warmed_subjects,
            failed_subjects=failed_subjects,
            course_bootstrap=course_bootstrap,
        )
        output = self._write_cached_bootstrap(cache_key=cache_key, payload=payload)
        log_timed_event(
            logger,
            "dashboard.bootstrap",
            started_at,
            cache_hit=False,
            student_id=student_id,
            requested_subject=subject or "auto",
            active_subject=active_subject or "none",
            course_bootstrap_source=course_bootstrap_source,
            warmed_subjects=len(warmed_subjects),
            failed_subjects=len(failed_subjects),
        )
        return output
