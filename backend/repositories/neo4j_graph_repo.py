from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class Neo4jGraphRepositoryError(RuntimeError):
    """Raised when Neo4j access fails."""


@dataclass
class Neo4jGraphConfig:
    uri: str
    user: str
    password: str

    @property
    def is_configured(self) -> bool:
        return bool(self.uri and self.user and self.password)


class Neo4jGraphRepository:
    """Small Neo4j adapter for section-3/5 graph context and mastery updates."""

    def __init__(self, config: Neo4jGraphConfig):
        self.config = config
        self._driver = None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def _ensure_driver(self):
        if self._driver is not None:
            return self._driver

        try:
            from neo4j import GraphDatabase
        except ModuleNotFoundError as exc:
            raise Neo4jGraphRepositoryError(
                "Neo4j driver not installed. Install `neo4j` package in backend environment."
            ) from exc

        try:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
            )
            return self._driver
        except Exception as exc:
            raise Neo4jGraphRepositoryError(f"Failed to initialize Neo4j driver: {exc}") from exc

    def _run(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        params = params or {}
        driver = self._ensure_driver()
        try:
            with driver.session() as session:
                result = session.run(cypher, params)
                return [row.data() for row in result]
        except Exception as exc:
            raise Neo4jGraphRepositoryError(f"Neo4j query failed: {exc}") from exc

    def ensure_topic_concepts(
        self,
        *,
        subject: str,
        sss_level: str,
        term: int,
        topic_ids: list[str],
    ) -> None:
        if not topic_ids:
            return
        self._run(
            """
            UNWIND $topic_ids AS topic_id
            MERGE (t:Topic {id: topic_id})
            SET t.subject = $subject, t.sss_level = $sss_level, t.term = $term
            MERGE (c:Concept {id: topic_id})
            SET c.subject = $subject, c.sss_level = $sss_level, c.term = $term
            MERGE (t)-[:COVERS]->(c)
            WITH t, c
            OPTIONAL MATCH (t)-[legacy:MAPS_TO]->(c)
            DELETE legacy
            """,
            {
                "topic_ids": topic_ids,
                "subject": subject,
                "sss_level": sss_level,
                "term": term,
            },
        )

    def remove_legacy_maps_to_edges(self) -> None:
        """Cleanup helper to remove old Topic-[:MAPS_TO]->Concept edges."""
        self._run(
            """
            MATCH (:Topic)-[r:MAPS_TO]->(:Concept)
            DELETE r
            """
        )

    def ensure_concepts(
        self,
        *,
        subject: str,
        sss_level: str,
        term: int,
        concept_ids: list[str],
    ) -> None:
        if not concept_ids:
            return
        self._run(
            """
            UNWIND $concept_ids AS concept_id
            MERGE (c:Concept {id: concept_id})
            SET c.subject = $subject, c.sss_level = $sss_level, c.term = $term
            """,
            {
                "concept_ids": concept_ids,
                "subject": subject,
                "sss_level": sss_level,
                "term": term,
            },
        )

    def ensure_prerequisite_chain(self, *, concept_ids: list[str]) -> None:
        if len(concept_ids) <= 1:
            return
        self._run(
            """
            UNWIND range(0, size($concept_ids) - 2) AS idx
            MATCH (a:Concept {id: $concept_ids[idx]}), (b:Concept {id: $concept_ids[idx + 1]})
            MERGE (a)-[:PREREQUISITE_OF]->(b)
            """,
            {"concept_ids": concept_ids},
        )

    def get_prerequisite_edges(self, *, concept_ids: list[str]) -> list[tuple[str, str]]:
        if not concept_ids:
            return []
        rows = self._run(
            """
            MATCH (p:Concept)-[:PREREQUISITE_OF]->(c:Concept)
            WHERE p.id IN $concept_ids AND c.id IN $concept_ids
            RETURN p.id AS prerequisite_concept_id, c.id AS concept_id
            """,
            {"concept_ids": concept_ids},
        )
        return [
            (str(row["prerequisite_concept_id"]), str(row["concept_id"]))
            for row in rows
            if row.get("prerequisite_concept_id") and row.get("concept_id")
        ]

    def get_mastery_map(
        self,
        *,
        student_id: str,
        subject: str,
        sss_level: str,
        term: int,
        concept_ids: list[str] | None = None,
    ) -> dict[str, float]:
        params: dict[str, Any] = {
            "student_id": student_id,
            "subject": subject,
            "sss_level": sss_level,
            "term": term,
            "concept_ids": concept_ids or [],
            "has_filter": bool(concept_ids),
        }
        rows = self._run(
            """
            MATCH (s:Student {id: $student_id})-[r:HAS_MASTERY]->(c:Concept)
            WHERE c.subject = $subject AND c.sss_level = $sss_level AND c.term = $term
              AND ($has_filter = false OR c.id IN $concept_ids)
            RETURN c.id AS concept_id, coalesce(r.score, 0.0) AS score
            """,
            params,
        )
        return {
            str(row["concept_id"]): float(row.get("score", 0.0))
            for row in rows
            if row.get("concept_id")
        }

    def upsert_mastery(
        self,
        *,
        student_id: str,
        concept_id: str,
        score: float,
        source: str,
        evaluated_at: datetime,
    ) -> None:
        self._run(
            """
            MERGE (s:Student {id: $student_id})
            MERGE (c:Concept {id: $concept_id})
            MERGE (s)-[r:HAS_MASTERY]->(c)
            SET r.score = $score,
                r.source = $source,
                r.last_evaluated_at = $evaluated_at
            """,
            {
                "student_id": student_id,
                "concept_id": concept_id,
                "score": max(0.0, min(1.0, float(score))),
                "source": source,
                "evaluated_at": evaluated_at.isoformat(),
            },
        )

    def record_update_event(
        self,
        *,
        student_id: str,
        quiz_id: str | None,
        attempt_id: str | None,
        subject: str,
        sss_level: str,
        term: int,
        source: str,
        concept_breakdown: list[dict[str, Any]],
    ) -> None:
        self._run(
            """
            CREATE (e:MasteryUpdateEvent {
                student_id: $student_id,
                quiz_id: $quiz_id,
                attempt_id: $attempt_id,
                subject: $subject,
                sss_level: $sss_level,
                term: $term,
                source: $source,
                concept_breakdown: $concept_breakdown,
                created_at: $created_at
            })
            """,
            {
                "student_id": student_id,
                "quiz_id": quiz_id,
                "attempt_id": attempt_id,
                "subject": subject,
                "sss_level": sss_level,
                "term": term,
                "source": source,
                "concept_breakdown": concept_breakdown,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
