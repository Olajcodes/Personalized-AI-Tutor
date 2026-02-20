"""Resolve curriculum scope: Student+Subject+Term → allowed topics/LOs."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from core_engine.curriculum.policies import assert_jss_level_allowed, assert_term_allowed
from core_engine.integrations.postgres_repo import PostgresRepo


@dataclass(frozen=True)
class CurriculumScope:
    subject_id: str
    jss_level: str
    term: int
    allowed_topic_ids: List[str]
    learning_objective_ids: List[str]


class CurriculumResolver:
    def __init__(self, repo: PostgresRepo):
        self.repo = repo

    def resolve_scope(self, *, subject_id: str, jss_level: str, term: int, topic_id: Optional[str] = None) -> CurriculumScope:
        assert_jss_level_allowed(jss_level)
        assert_term_allowed(term)

        topics = self.repo.list_topics(subject_id=subject_id, jss_level=jss_level, term=term)
        allowed_topic_ids = [t["id"] for t in topics]

        if topic_id is not None and topic_id not in allowed_topic_ids:
            raise ValueError("topic_id not allowed for this student scope (subject/jss/term).")

        lo_ids = self.repo.list_learning_objective_ids(topic_ids=allowed_topic_ids)

        return CurriculumScope(
            subject_id=subject_id,
            jss_level=jss_level,
            term=term,
            allowed_topic_ids=allowed_topic_ids,
            learning_objective_ids=lo_ids,
        )
