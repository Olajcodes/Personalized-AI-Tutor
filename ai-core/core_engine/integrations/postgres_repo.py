"""Minimal Postgres repository methods (MVP)."""

from __future__ import annotations
from typing import Any, Dict, List


class PostgresRepo:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def list_topics(self, *, subject_id: str, jss_level: str, term: int) -> List[Dict[str, Any]]:
        """SELECT topics for (subject_id, jss_level, term)."""
        return []

    def list_learning_objective_ids(self, *, topic_ids: List[str]) -> List[str]:
        """SELECT learning objective IDs for given topic IDs."""
        return []

    def upsert_topic_mastery(self, *, user_id: str, subject_id: str, topic_id: str, mastery_delta: float) -> None:
        """UPSERT mastery record and increment by mastery_delta."""
        pass
