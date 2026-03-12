from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.repositories.graph_repo import GraphRepository
from backend.repositories.tutor_session_repo import TutorSessionRepository
from backend.schemas.tutor_schema import (
    TutorPendingAssessmentOut,
    TutorQuickActionOut,
    TutorSessionBootstrapIn,
    TutorSessionBootstrapOut,
)
from backend.services.lesson_graph_service import lesson_graph_service
from backend.services.lesson_service import fetch_topic_lesson
from backend.services.tutor_assessment_service import TutorAssessmentService

BOOTSTRAP_CACHE_TTL_SECONDS = 30.0
_BOOTSTRAP_CACHE: dict[str, tuple[float, TutorSessionBootstrapOut]] = {}
TOPIC_SNAPSHOT_CACHE_TTL_SECONDS = 180.0
_TOPIC_SNAPSHOT_CACHE: dict[str, tuple[float, "_TopicSnapshot"]] = {}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _TopicSnapshot:
    lesson: dict
    graph_context: object
    why_this_topic: str | None
    next_unlock: object | None
    graph_nodes: list
    graph_edges: list


class LessonExperienceService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = TutorSessionRepository(db)
        self.assessment_service = TutorAssessmentService(db)

    def _get_or_create_session(self, *, payload: TutorSessionBootstrapIn) -> tuple[UUID, bool]:
        if payload.session_id and self.session_repo.session_exists_for_student(
            session_id=payload.session_id,
            student_id=payload.student_id,
        ):
            return payload.session_id, False

        row = self.session_repo.create_session(
            student_id=payload.student_id,
            subject=payload.subject,
            term=int(payload.term),
        )
        return UUID(str(row["id"])), True

    @staticmethod
    def _cache_key(*, payload: TutorSessionBootstrapIn, session_id: UUID) -> str:
        return ":".join(
            [
                str(payload.student_id),
                payload.subject,
                payload.sss_level,
                str(payload.term),
                str(payload.topic_id),
                str(session_id),
            ]
        )

    @staticmethod
    def _topic_snapshot_key(
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: UUID,
        mastery_signature: str,
    ) -> str:
        return ":".join(
            [
                str(student_id),
                subject,
                sss_level,
                str(term),
                str(topic_id),
                mastery_signature,
            ]
        )

    @staticmethod
    def _read_cached_bootstrap(*, cache_key: str) -> TutorSessionBootstrapOut | None:
        entry = _BOOTSTRAP_CACHE.get(cache_key)
        if entry is None:
            return None
        created_at, payload = entry
        if (time.time() - created_at) > BOOTSTRAP_CACHE_TTL_SECONDS:
            _BOOTSTRAP_CACHE.pop(cache_key, None)
            return None
        return payload

    @staticmethod
    def _write_cached_bootstrap(*, cache_key: str, payload: TutorSessionBootstrapOut) -> TutorSessionBootstrapOut:
        _BOOTSTRAP_CACHE[cache_key] = (time.time(), payload)
        return payload

    @staticmethod
    def _read_cached_topic_snapshot(*, cache_key: str) -> _TopicSnapshot | None:
        entry = _TOPIC_SNAPSHOT_CACHE.get(cache_key)
        if entry is None:
            return None
        created_at, payload = entry
        if (time.time() - created_at) > TOPIC_SNAPSHOT_CACHE_TTL_SECONDS:
            _TOPIC_SNAPSHOT_CACHE.pop(cache_key, None)
            return None
        return payload

    @staticmethod
    def _write_cached_topic_snapshot(*, cache_key: str, payload: _TopicSnapshot) -> _TopicSnapshot:
        _TOPIC_SNAPSHOT_CACHE[cache_key] = (time.time(), payload)
        return payload

    @staticmethod
    def _scope_mastery_signature(
        *,
        db: Session,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
    ) -> str:
        mastery_map = GraphRepository(db).get_mastery_map(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        )
        if not mastery_map:
            return "no_mastery"
        payload = json.dumps(sorted(mastery_map.items()), separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def invalidate_topic_snapshot_cache(
        cls,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: UUID | None = None,
    ) -> None:
        prefix = ":".join([str(student_id), subject, sss_level, str(term)])
        for key in list(_TOPIC_SNAPSHOT_CACHE.keys()):
            if not key.startswith(prefix):
                continue
            if topic_id is not None and f":{topic_id}:" not in key:
                continue
            _TOPIC_SNAPSHOT_CACHE.pop(key, None)

    @staticmethod
    def invalidate_session_cache(*, session_id: UUID) -> None:
        session_token = f":{session_id}"
        for key in [cache_key for cache_key in list(_BOOTSTRAP_CACHE.keys()) if cache_key.endswith(session_token)]:
            _BOOTSTRAP_CACHE.pop(key, None)

    @classmethod
    def _build_topic_snapshot(
        cls,
        *,
        db: Session,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: UUID,
    ) -> tuple[_TopicSnapshot, str]:
        mastery_signature = cls._scope_mastery_signature(
            db=db,
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        )
        cache_key = cls._topic_snapshot_key(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
            mastery_signature=mastery_signature,
        )
        cached = cls._read_cached_topic_snapshot(cache_key=cache_key)
        if cached is not None:
            return cached, "cache"

        lesson = fetch_topic_lesson(db=db, topic_id=topic_id, student_id=student_id)
        graph_context = lesson_graph_service.get_lesson_graph_context(
            db,
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
        )
        snapshot = _TopicSnapshot(
            lesson=lesson,
            graph_context=graph_context,
            why_this_topic=graph_context.why_this_matters,
            next_unlock=graph_context.next_unlock,
            graph_nodes=list(graph_context.graph_nodes),
            graph_edges=list(graph_context.graph_edges),
        )
        cls._write_cached_topic_snapshot(cache_key=cache_key, payload=snapshot)
        return snapshot, "fresh"

    @classmethod
    def prewarm_topics(
        cls,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_ids: list[UUID],
    ) -> dict[str, list[str]]:
        result = {
            "warmed_topic_ids": [],
            "cache_hit_topic_ids": [],
            "failed_topic_ids": [],
        }
        if not topic_ids:
            return result
        db = SessionLocal()
        try:
            seen: set[str] = set()
            for topic_id in topic_ids:
                topic_token = str(topic_id)
                if not topic_token or topic_token in seen:
                    continue
                seen.add(topic_token)
                try:
                    _, source = cls._build_topic_snapshot(
                        db=db,
                        student_id=student_id,
                        subject=subject,
                        sss_level=sss_level,
                        term=term,
                        topic_id=topic_id,
                    )
                    logger.info(
                        "lesson.bootstrap.prewarm_success student_id=%s topic_id=%s subject=%s level=%s term=%s source=%s",
                        student_id,
                        topic_id,
                        subject,
                        sss_level,
                        term,
                        source,
                    )
                    if source == "cache":
                        result["cache_hit_topic_ids"].append(topic_token)
                    else:
                        result["warmed_topic_ids"].append(topic_token)
                except Exception as exc:  # pragma: no cover - best effort prewarm
                    db.rollback()
                    logger.warning(
                        "lesson.bootstrap.prewarm_failed student_id=%s topic_id=%s detail=%s",
                        student_id,
                        topic_id,
                        exc,
                    )
                    result["failed_topic_ids"].append(topic_token)
        finally:
            db.close()
        return result

    @staticmethod
    def _suggested_actions(topic_title: str) -> list[TutorQuickActionOut]:
        return [
            TutorQuickActionOut(
                id="teach-simple",
                label="Explain Simpler",
                prompt=f"Teach {topic_title} like I am new to it and keep it step-by-step.",
                icon="sparkles",
                intent="teach",
            ),
            TutorQuickActionOut(
                id="real-life-example",
                label="Real-life Example",
                prompt=f"Give me one real-life example that makes {topic_title} easy to understand.",
                icon="lightbulb",
                intent="teach",
            ),
            TutorQuickActionOut(
                id="why-this-topic",
                label="Why This Topic?",
                prompt=f"Why am I learning {topic_title} now, and what does it unlock next?",
                icon="git-branch",
                intent="diagnose",
            ),
            TutorQuickActionOut(
                id="checkpoint",
                label="1-Min Checkpoint",
                prompt=f"Ask me one focused question on {topic_title}.",
                icon="target",
                intent="assessment_start",
            ),
            TutorQuickActionOut(
                id="prereq-bridge",
                label="Connect to Previous Topic",
                prompt=f"Bridge the prerequisite idea I need before mastering {topic_title}.",
                icon="route",
                intent="socratic",
            ),
            TutorQuickActionOut(
                id="common-mistake",
                label="Common Mistake",
                prompt=f"Show me a common mistake students make in {topic_title} and fix it.",
                icon="shield-alert",
                intent="diagnose",
            ),
            TutorQuickActionOut(
                id="waec-mode",
                label="WAEC Mode",
                prompt=f"Give me one WAEC-style coaching explanation for {topic_title}.",
                icon="graduation-cap",
                intent="exam-practice",
            ),
            TutorQuickActionOut(
                id="recap",
                label="Recap",
                prompt=f"Recap {topic_title} in three sharp points and one memory hook.",
                icon="notebook-pen",
                intent="recap",
            ),
        ]

    def bootstrap(self, payload: TutorSessionBootstrapIn) -> TutorSessionBootstrapOut:
        session_id, session_started = self._get_or_create_session(payload=payload)
        cache_key = self._cache_key(payload=payload, session_id=session_id)
        cached = self._read_cached_bootstrap(cache_key=cache_key)
        if cached is not None:
            if session_started:
                return cached.model_copy(update={"session_started": True, "session_id": session_id})
            return cached

        snapshot, _ = self._build_topic_snapshot(
            db=self.db,
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=int(payload.term),
            topic_id=payload.topic_id,
        )
        lesson = snapshot.lesson
        graph_context = snapshot.graph_context
        pending_state = self.assessment_service.get_pending_assessment(session_id=session_id)
        pending_assessment = None
        if pending_state is not None:
            pending_assessment = TutorPendingAssessmentOut(
                assessment_id=UUID(str(pending_state["assessment_id"])),
                question=str(pending_state.get("question") or ""),
                concept_id=str(pending_state.get("concept_id") or ""),
                concept_label=str(pending_state.get("concept_label") or ""),
                hint=str(pending_state.get("hint") or "").strip() or None,
                difficulty=str(pending_state.get("difficulty") or "").strip() or None,
            )

        greeting = (
            f"You are in {lesson.get('title')}. "
            f"Your weakest focus here is {graph_context.weakest_concepts[0].label if graph_context.weakest_concepts else 'the current lesson core idea'}, "
            "and the graph is showing what unlocks next."
        )
        bootstrap = TutorSessionBootstrapOut(
            session_id=session_id,
            session_started=session_started,
            greeting=greeting,
            topic_id=payload.topic_id,
            lesson=lesson,
            graph_context=graph_context,
            suggested_actions=self._suggested_actions(graph_context.topic_title),
            pending_assessment=pending_assessment,
            next_unlock=snapshot.next_unlock,
            why_this_topic=snapshot.why_this_topic,
            graph_nodes=snapshot.graph_nodes,
            graph_edges=snapshot.graph_edges,
            assessment_ready=bool(graph_context.current_concepts),
        )
        return self._write_cached_bootstrap(cache_key=cache_key, payload=bootstrap)


lesson_experience_service = LessonExperienceService
