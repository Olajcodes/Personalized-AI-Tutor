from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


class InternalPostgresRepository:
    def __init__(self, db: Session):
        self.db = db

    def _table_exists(self, table_name: str) -> bool:
        return inspect(self.db.bind).has_table(table_name)

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        inspector = inspect(self.db.bind)
        if not inspector.has_table(table_name):
            return False
        return any(col["name"] == column_name for col in inspector.get_columns(table_name))

    def get_profile_context(self, *, student_id: UUID) -> dict:
        row = self.db.execute(
            text(
                """
                SELECT id, student_id, sss_level, active_term
                FROM student_profiles
                WHERE student_id = :student_id
                """
            ),
            {"student_id": student_id},
        ).mappings().first()
        if not row:
            return {}

        profile_id = row["id"]

        subject_rows = self.db.execute(
            text(
                """
                SELECT s.slug
                FROM student_subjects ss
                JOIN subjects s ON s.id = ss.subject_id
                WHERE ss.student_profile_id = :profile_id
                ORDER BY s.slug
                """
            ),
            {"profile_id": profile_id},
        ).mappings().all()

        pref_row = self.db.execute(
            text(
                """
                SELECT explanation_depth, examples_first, pace
                FROM learning_preferences
                WHERE student_profile_id = :profile_id
                """
            ),
            {"profile_id": profile_id},
        ).mappings().first()

        return {
            "student_id": row["student_id"],
            "profile_id": row["id"],
            "sss_level": row["sss_level"],
            "term": row["active_term"],
            "subjects": [r["slug"] for r in subject_rows],
            "preferences": dict(pref_row) if pref_row else None,
        }

    def get_history(self, *, student_id: UUID, session_id: UUID) -> list[dict]:
        rows = self.db.execute(
            text(
                """
                SELECT tm.id, tm.role, tm.content, tm.created_at
                FROM tutor_messages tm
                JOIN tutor_sessions ts ON ts.id = tm.session_id
                WHERE ts.id = :session_id
                  AND ts.student_id = :student_id
                ORDER BY tm.created_at ASC
                """
            ),
            {"session_id": session_id, "student_id": student_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    def save_quiz_attempt(self, payload: dict) -> dict:
        if not self._table_exists("internal_quiz_attempts"):
            raise RuntimeError("internal_quiz_attempts table is missing. Apply Section 2 migrations.")

        attempt_id = payload.get("attempt_id") or uuid.uuid4()
        row = self.db.execute(
            text(
                """
                INSERT INTO internal_quiz_attempts (
                    attempt_id, quiz_id, student_id, subject, sss_level, term,
                    answers, time_taken_seconds, score, created_at
                )
                VALUES (
                    :attempt_id, :quiz_id, :student_id, :subject, :sss_level, :term,
                    CAST(:answers AS JSONB), :time_taken_seconds, :score, NOW()
                )
                RETURNING attempt_id, created_at
                """
            ),
            {
                "attempt_id": attempt_id,
                "quiz_id": payload["quiz_id"],
                "student_id": payload["student_id"],
                "subject": payload["subject"],
                "sss_level": payload["sss_level"],
                "term": payload["term"],
                "answers": payload["answers_json"],
                "time_taken_seconds": payload["time_taken_seconds"],
                "score": payload.get("score"),
            },
        ).mappings().first()
        self.db.commit()
        return dict(row) if row else {}

    def get_class_roster(self, *, class_id: UUID) -> list[UUID]:
        if not self._table_exists("class_enrollments"):
            return []

        status_filter = ""
        if self._column_exists("class_enrollments", "status"):
            status_filter = " AND status = 'active'"

        rows = self.db.execute(
            text(
                f"""
                SELECT student_id
                FROM class_enrollments
                WHERE class_id = :class_id
                {status_filter}
                ORDER BY student_id
                """
            ),
            {"class_id": class_id},
        ).mappings().all()
        return [row["student_id"] for row in rows]
