from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class TutorSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, *, student_id: UUID, subject: str, term: int) -> dict:
        session_id = uuid.uuid4()
        row = self.db.execute(
            text(
                """
                INSERT INTO tutor_sessions (
                    id, student_id, subject, term, status, started_at, created_at, updated_at
                )
                VALUES (
                    :id, :student_id, :subject, :term, 'active', NOW(), NOW(), NOW()
                )
                RETURNING id, student_id, subject, term, started_at
                """
            ),
            {
                "id": session_id,
                "student_id": student_id,
                "subject": subject,
                "term": term,
            },
        ).mappings().first()
        self.db.commit()
        return dict(row) if row else {}

    def session_exists_for_student(self, *, session_id: UUID, student_id: UUID) -> bool:
        row = self.db.execute(
            text(
                """
                SELECT 1
                FROM tutor_sessions
                WHERE id = :session_id
                  AND student_id = :student_id
                """
            ),
            {"session_id": session_id, "student_id": student_id},
        ).first()
        return row is not None

    def get_session_history(self, *, session_id: UUID) -> list[dict]:
        rows = self.db.execute(
            text(
                """
                SELECT id, role, content, created_at
                FROM tutor_messages
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                """
            ),
            {"session_id": session_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    def end_session(
        self,
        *,
        session_id: UUID,
        student_id: UUID,
        total_tokens: int | None,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        cost_usd: float | None,
        end_reason: str | None,
    ) -> dict:
        row = self.db.execute(
            text(
                """
                UPDATE tutor_sessions
                SET
                    status = 'ended',
                    ended_at = NOW(),
                    duration_seconds = GREATEST(
                        0,
                        CAST(EXTRACT(EPOCH FROM (NOW() - started_at)) AS INTEGER)
                    ),
                    total_tokens = COALESCE(:total_tokens, total_tokens),
                    prompt_tokens = COALESCE(:prompt_tokens, prompt_tokens),
                    completion_tokens = COALESCE(:completion_tokens, completion_tokens),
                    cost_usd = COALESCE(:cost_usd, cost_usd),
                    end_reason = COALESCE(:end_reason, end_reason),
                    updated_at = NOW()
                WHERE id = :session_id
                  AND student_id = :student_id
                RETURNING id, status, ended_at, duration_seconds, total_tokens, prompt_tokens, completion_tokens, cost_usd
                """
            ),
            {
                "session_id": session_id,
                "student_id": student_id,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cost_usd": cost_usd,
                "end_reason": end_reason,
            },
        ).mappings().first()
        self.db.commit()
        return dict(row) if row else {}
