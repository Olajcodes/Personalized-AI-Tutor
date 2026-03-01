"""Postgres repository methods used by ai-core orchestration."""

from __future__ import annotations

from typing import Any, Dict, List


class PostgresRepoError(RuntimeError):
    """Raised when Postgres query execution fails."""


class PostgresRepo:
    def __init__(self, dsn: str):
        self.dsn = (dsn or "").strip()
        if not self.dsn:
            raise PostgresRepoError("POSTGRES_DSN is required for ai-core Postgres access.")

    def _connect(self):
        try:
            import psycopg
        except ModuleNotFoundError as exc:
            raise PostgresRepoError("psycopg dependency missing in ai-core environment.") from exc

        return psycopg.connect(self.dsn)

    def list_topics(self, *, subject_id: str, sss_level: str, term: int) -> List[Dict[str, Any]]:
        """Return approved topic IDs and titles for a subject/level/term scope."""
        sql = """
            SELECT id::text AS id, title
            FROM topics
            WHERE subject_id = %s::uuid
              AND sss_level = %s
              AND term = %s
              AND is_approved = TRUE
            ORDER BY title ASC
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (subject_id, sss_level, term))
                    rows = cursor.fetchall()
        except Exception as exc:
            raise PostgresRepoError(f"Failed to list scoped topics: {exc}") from exc

        return [{"id": row[0], "title": row[1]} for row in rows]

    def list_learning_objective_ids(self, *, topic_ids: List[str]) -> List[str]:
        """Return concept IDs mapped to supplied topic IDs."""
        if not topic_ids:
            return []

        sql = """
            SELECT DISTINCT concept_id
            FROM curriculum_topic_maps
            WHERE topic_id = ANY(%s::uuid[])
              AND concept_id IS NOT NULL
            ORDER BY concept_id ASC
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (topic_ids,))
                    rows = cursor.fetchall()
        except Exception as exc:
            raise PostgresRepoError(f"Failed to list learning objective IDs: {exc}") from exc

        return [str(row[0]) for row in rows if row[0]]

    def _resolve_subject_slug(self, cursor, subject_id: str) -> str:
        """Resolve subject slug from ID; fallback to provided value if already slug."""
        sql = "SELECT slug FROM subjects WHERE id = %s::uuid LIMIT 1"
        cursor.execute(sql, (subject_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return str(row[0])
        return subject_id

    def _resolve_student_scope(self, cursor, user_id: str) -> tuple[str, int]:
        """Resolve student's active learning scope; fallback to SSS1 term 1."""
        sql = """
            SELECT sss_level, active_term
            FROM student_profiles
            WHERE student_id = %s::uuid
            LIMIT 1
        """
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        if row:
            return str(row[0]), int(row[1])
        return "SSS1", 1

    def upsert_topic_mastery(
        self, *, user_id: str, subject_id: str, topic_id: str, mastery_delta: float
    ) -> None:
        """Upsert concept mastery row using topic ID as concept anchor."""
        upsert_sql = """
            INSERT INTO student_concept_mastery (
                student_id, subject, sss_level, term, concept_id, mastery_score, source, last_evaluated_at
            )
            VALUES (
                %s::uuid, %s, %s, %s, %s, GREATEST(0.0, LEAST(1.0, %s)), 'practice', NOW()
            )
            ON CONFLICT (student_id, subject, sss_level, term, concept_id)
            DO UPDATE
            SET mastery_score = GREATEST(
                0.0,
                LEAST(1.0, student_concept_mastery.mastery_score + EXCLUDED.mastery_score)
            ),
            source = EXCLUDED.source,
            last_evaluated_at = NOW(),
            updated_at = NOW()
        """
        try:
            with self._connect() as conn:
                with conn.cursor() as cursor:
                    subject_slug = self._resolve_subject_slug(cursor, subject_id)
                    sss_level, term = self._resolve_student_scope(cursor, user_id)
                    cursor.execute(
                        upsert_sql,
                        (
                            user_id,
                            subject_slug,
                            sss_level,
                            term,
                            topic_id,
                            float(mastery_delta),
                        ),
                    )
                conn.commit()
        except Exception as exc:
            raise PostgresRepoError(f"Failed to upsert topic mastery: {exc}") from exc
