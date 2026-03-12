from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.student import StudentProfile, StudentSubject
from backend.models.subject import Subject
from backend.schemas.dashboard_schema import DashboardBootstrapOut
from backend.services.course_experience_service import CourseExperienceService


class DashboardExperienceError(ValueError):
    pass


class DashboardExperienceService:
    def __init__(self, db: Session):
        self.db = db
        self.course_service = CourseExperienceService(db)

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
        profile, available_subjects = self._profile_and_subjects(student_id=student_id)
        course_bootstrap = None
        active_subject = subject if subject in available_subjects else None

        if active_subject is None:
            latest = self.course_service.latest_intervention_bootstrap(student_id=student_id)
            if latest is not None:
                course_bootstrap = latest
                active_subject = latest.subject

        if active_subject is None and available_subjects:
            active_subject = available_subjects[0]

        if active_subject is not None and course_bootstrap is None:
            course_bootstrap = self.course_service.bootstrap(
                student_id=student_id,
                subject=active_subject,
                term=int(profile.active_term),
            )

        return DashboardBootstrapOut(
            student_id=student_id,
            sss_level=str(profile.sss_level),  # type: ignore[arg-type]
            term=int(profile.active_term),  # type: ignore[arg-type]
            available_subjects=available_subjects,
            active_subject=active_subject,
            course_bootstrap=course_bootstrap,
        )
