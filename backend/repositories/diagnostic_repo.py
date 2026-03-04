from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from backend.models.curriculum_topic_map import CurriculumTopicMap
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

    def get_scope_topic_concept_rows(
        self,
        *,
        subject: str,
        sss_level: str,
        term: int,
    ) -> list[dict]:
        """Return scoped topic->concept rows with explicit prereq IDs when available.

        Each row includes:
        - topic_id
        - topic_title
        - concept_id
        - prereq_concept_ids (possibly empty)
        """
        topics = self.get_scope_topics(subject=subject, sss_level=sss_level, term=term)
        rows: list[dict] = []

        for topic in topics:
            map_query = self.db.query(CurriculumTopicMap).filter(CurriculumTopicMap.topic_id == topic.id)
            if topic.curriculum_version_id is not None:
                map_query = map_query.filter(CurriculumTopicMap.version_id == topic.curriculum_version_id)
            mappings = map_query.order_by(CurriculumTopicMap.updated_at.desc(), CurriculumTopicMap.created_at.desc()).all()

            seen_concepts: set[str] = set()
            for mapping in mappings:
                concept_id = str(mapping.concept_id or "").strip()
                if not concept_id or concept_id in seen_concepts:
                    continue
                seen_concepts.add(concept_id)
                prereq_ids = [str(value).strip() for value in (mapping.prereq_concept_ids or []) if str(value).strip()]
                rows.append(
                    {
                        "topic_id": str(topic.id),
                        "topic_title": str(topic.title),
                        "concept_id": concept_id,
                        "prereq_concept_ids": prereq_ids,
                    }
                )

            if not seen_concepts:
                # Fallback topic-as-concept when curriculum map is not available yet.
                rows.append(
                    {
                        "topic_id": str(topic.id),
                        "topic_title": str(topic.title),
                        "concept_id": str(topic.id),
                        "prereq_concept_ids": [],
                    }
                )

        return rows

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
