from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.diagnostic import Diagnostic
from backend.models.diagnostic_attempt import DiagnosticAttempt
from backend.models.student import StudentProfile, StudentSubject
from backend.models.subject import Subject
from backend.models.topic import Topic


class DiagnosticRepository:
    def __init__(self, db: Session):
        self.db = db

    def validate_student_scope(self, *, student_id: UUID, subject: str, sss_level: str, term: int) -> bool:
        profile = (
            self.db.query(StudentProfile)
            .filter(StudentProfile.student_id == student_id)
            .first()
        )
        if not profile:
            return False
        if profile.sss_level != sss_level or int(profile.active_term) != int(term):
            return False

        subject_row = self.db.query(Subject).filter(Subject.slug == subject).first()
        if not subject_row:
            return False

        enrollment = (
            self.db.query(StudentSubject)
            .filter(
                StudentSubject.student_profile_id == profile.id,
                StudentSubject.subject_id == subject_row.id,
            )
            .first()
        )
        return enrollment is not None

    def get_scope_topics(self, *, subject: str, sss_level: str, term: int) -> list[Topic]:
        return (
            self.db.query(Topic)
            .join(Subject, Subject.id == Topic.subject_id)
            .filter(
                Subject.slug == subject,
                Topic.sss_level == sss_level,
                Topic.term == term,
                Topic.is_approved.is_(True),
            )
            .order_by(Topic.created_at.asc(), Topic.title.asc())
            .all()
        )

    def create_diagnostic(
        self,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        concept_targets: list[str],
        questions: list[dict],
    ) -> Diagnostic:
        diagnostic = Diagnostic(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            status="started",
            concept_targets=concept_targets,
            questions=questions,
        )
        self.db.add(diagnostic)
        self.db.flush()
        return diagnostic

    def get_diagnostic(self, *, diagnostic_id: UUID, student_id: UUID) -> Diagnostic | None:
        return (
            self.db.query(Diagnostic)
            .filter(Diagnostic.id == diagnostic_id, Diagnostic.student_id == student_id)
            .first()
        )

    def save_attempt(
        self,
        *,
        diagnostic_id: UUID,
        student_id: UUID,
        answers: list[dict],
        baseline_mastery_updates: list[dict],
        recommended_start_topic_id: str | None,
        score: float,
    ) -> DiagnosticAttempt:
        existing = (
            self.db.query(DiagnosticAttempt)
            .filter(DiagnosticAttempt.diagnostic_id == diagnostic_id)
            .first()
        )
        if existing:
            existing.answers = answers
            existing.baseline_mastery_updates = baseline_mastery_updates
            existing.recommended_start_topic_id = recommended_start_topic_id
            existing.score = score
            self.db.flush()
            return existing

        attempt = DiagnosticAttempt(
            diagnostic_id=diagnostic_id,
            student_id=student_id,
            answers=answers,
            baseline_mastery_updates=baseline_mastery_updates,
            recommended_start_topic_id=recommended_start_topic_id,
            score=score,
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def mark_submitted(self, diagnostic: Diagnostic) -> None:
        diagnostic.status = "submitted"
        self.db.flush()
