from __future__ import annotations

import json
from uuid import UUID

from backend.repositories.internal_postgres_repo import InternalPostgresRepository
from backend.schemas.internal_postgres_schema import (
    InternalClassRosterOut,
    InternalHistoryOut,
    InternalProfileOut,
    InternalQuizAttemptIn,
    InternalQuizAttemptOut,
)
from backend.schemas.tutor_session_schema import SessionMessageOut


class InternalProfileNotFoundError(ValueError):
    pass


class InternalPostgresService:
    def __init__(self, repo: InternalPostgresRepository):
        self.repo = repo

    def get_profile(self, student_id: UUID) -> InternalProfileOut:
        row = self.repo.get_profile_context(student_id=student_id)
        if not row:
            raise InternalProfileNotFoundError("Student profile not found.")
        return InternalProfileOut(
            student_id=row["student_id"],
            profile_id=row["profile_id"],
            sss_level=row["sss_level"],
            term=row["term"],
            subjects=row["subjects"],
            preferences=row["preferences"],
        )

    def get_history(self, *, student_id: UUID, session_id: UUID) -> InternalHistoryOut:
        rows = self.repo.get_history(student_id=student_id, session_id=session_id)
        messages = [
            SessionMessageOut(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
        return InternalHistoryOut(
            session_id=session_id,
            student_id=student_id,
            messages=messages,
        )

    def store_quiz_attempt(self, payload: InternalQuizAttemptIn) -> InternalQuizAttemptOut:
        row = self.repo.save_quiz_attempt(
            {
                "attempt_id": payload.attempt_id,
                "quiz_id": payload.quiz_id,
                "student_id": payload.student_id,
                "subject": payload.subject,
                "sss_level": payload.sss_level,
                "term": payload.term,
                "answers_json": json.dumps([answer.model_dump() for answer in payload.answers]),
                "time_taken_seconds": payload.time_taken_seconds,
                "score": payload.score,
            }
        )
        if not row:
            raise RuntimeError("Failed to store quiz attempt.")
        return InternalQuizAttemptOut(
            attempt_id=row["attempt_id"],
            stored=True,
            created_at=row["created_at"],
        )

    def get_class_roster(self, class_id: UUID) -> InternalClassRosterOut:
        student_ids = self.repo.get_class_roster(class_id=class_id)
        return InternalClassRosterOut(class_id=class_id, student_ids=student_ids)
