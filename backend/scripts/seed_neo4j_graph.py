"""Seed Neo4j with a connected curriculum graph from Postgres scope + mappings.

Usage:
  python -m backend.scripts.seed_neo4j_graph

Optional env:
  NEO4J_SEED_STUDENT_ID=<uuid>  # seeds starter HAS_MASTERY links for demo student
  NEO4J_RESET_GRAPH=true        # clears existing Subject/Topic/Concept graph before reseed
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import TypedDict
from uuid import UUID

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.curriculum_topic_map import CurriculumTopicMap
from backend.models.subject import Subject
from backend.models.topic import Topic
from backend.models.lesson import Lesson  # noqa: F401  # ensure Topic<->Lesson mapper resolves
from backend.repositories.neo4j_graph_repo import (
    Neo4jGraphConfig,
    Neo4jGraphRepository,
    Neo4jGraphRepositoryError,
)


class TopicSeedEntry(TypedDict):
    topic_id: str
    title: str
    sss_level: str
    term: int
    concept_ids: list[str]


class ScopeSeedPayload(TypedDict):
    topics: dict[str, TopicSeedEntry]
    prereq_edges: set[tuple[str, str]]


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _topic_maps_for_topic(db: Session, topic: Topic) -> list[CurriculumTopicMap]:
    query = db.query(CurriculumTopicMap).filter(CurriculumTopicMap.topic_id == topic.id)
    if topic.curriculum_version_id is not None:
        query = query.filter(CurriculumTopicMap.version_id == topic.curriculum_version_id)
    rows = query.order_by(CurriculumTopicMap.updated_at.desc(), CurriculumTopicMap.created_at.desc()).all()

    deduped: list[CurriculumTopicMap] = []
    seen: set[str] = set()
    for row in rows:
        concept_id = str(row.concept_id or "").strip()
        if not concept_id or concept_id in seen:
            continue
        seen.add(concept_id)
        deduped.append(row)
    return deduped


def _build_scope_graph_payload(db: Session) -> dict[tuple[str, str, int], ScopeSeedPayload]:
    rows = (
        db.query(Topic, Subject.slug)
        .join(Subject, Subject.id == Topic.subject_id)
        .filter(Topic.is_approved.is_(True))
        .order_by(Subject.slug.asc(), Topic.sss_level.asc(), Topic.term.asc(), Topic.created_at.asc(), Topic.title.asc())
        .all()
    )
    grouped: dict[tuple[str, str, int], ScopeSeedPayload] = defaultdict(
        lambda: {"topics": {}, "prereq_edges": set()}
    )
    for topic, subject_slug in rows:
        scope_key = (str(subject_slug), str(topic.sss_level), int(topic.term))
        payload = grouped[scope_key]
        topics = payload["topics"]
        prereq_edges = payload["prereq_edges"]

        topic_id = str(topic.id)
        topic_entry = topics.setdefault(
            topic_id,
            {
                "topic_id": topic_id,
                "title": str(topic.title),
                "sss_level": str(topic.sss_level),
                "term": int(topic.term),
                "concept_ids": [],
            },
        )

        mappings = _topic_maps_for_topic(db, topic)
        if mappings:
            for mapping in mappings:
                concept_id = str(mapping.concept_id).strip()
                if concept_id not in topic_entry["concept_ids"]:
                    topic_entry["concept_ids"].append(concept_id)
                for prereq in mapping.prereq_concept_ids or []:
                    prereq_id = str(prereq).strip()
                    if prereq_id and prereq_id != concept_id:
                        prereq_edges.add((prereq_id, concept_id))
        else:
            # Fallback: treat topic as a single concept when no explicit mappings exist.
            if topic_id not in topic_entry["concept_ids"]:
                topic_entry["concept_ids"].append(topic_id)

    return grouped


def run() -> None:
    config = Neo4jGraphConfig(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    if not config.is_configured:
        raise RuntimeError("NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD must be set before seeding graph.")

    db: Session = SessionLocal()
    neo = Neo4jGraphRepository(config)
    seeded_scopes = 0
    seeded_topics = 0
    seeded_concepts = 0
    seeded_prereq_edges = 0
    try:
        if _is_truthy(os.getenv("NEO4J_RESET_GRAPH")):
            neo.reset_curriculum_subgraph()

        neo.remove_legacy_relationships()

        grouped = _build_scope_graph_payload(db)
        for (subject, sss_level, term), scope_payload in grouped.items():
            topics_map = scope_payload["topics"]
            prereq_edges = scope_payload["prereq_edges"]

            topics = list(topics_map.values())
            neo.ensure_subject_topics(subject=subject, topics=topics)

            flat_concepts: list[str] = []
            for topic in topics:
                concept_ids = [str(concept_id) for concept_id in topic["concept_ids"]]
                flat_concepts.extend(concept_ids)
                neo.ensure_topic_concept_links(
                    subject=subject,
                    sss_level=sss_level,
                    term=term,
                    topic_id=str(topic["topic_id"]),
                    topic_title=str(topic["title"]),
                    concept_ids=concept_ids,
                )

            if prereq_edges:
                edges = sorted(prereq_edges)
                neo.ensure_prerequisite_edges(edges=edges)
                seeded_prereq_edges += len(edges)
            else:
                # Fallback to sequential concept chain when explicit prerequisites are unavailable.
                neo.ensure_prerequisite_chain(concept_ids=flat_concepts)
                seeded_prereq_edges += max(len(flat_concepts) - 1, 0)

            seeded_scopes += 1
            seeded_topics += len(topics)
            seeded_concepts += len(set(flat_concepts))

        seed_student = os.getenv("NEO4J_SEED_STUDENT_ID", "").strip()
        if seed_student:
            student_uuid = str(UUID(seed_student))
            first_per_scope = []
            for (_, _, _), scope_payload in grouped.items():
                topics_map = scope_payload["topics"]
                topics = list(topics_map.values())
                if topics and topics[0]["concept_ids"]:
                    first_per_scope.append(str(topics[0]["concept_ids"][0]))
            if first_per_scope:
                # Give starter mastery to first concept in each scope for demo visualizations.
                for concept_id in first_per_scope:
                    neo.upsert_mastery(
                        student_id=student_uuid,
                        concept_id=concept_id,
                        score=0.2,
                        source="seed",
                        evaluated_at=datetime.now(timezone.utc),
                    )

        print(
            "Neo4j seed complete. "
            f"scopes={seeded_scopes}, topics={seeded_topics}, concepts={seeded_concepts}, prereq_edges={seeded_prereq_edges}"
        )
        if seed_student:
            print(f"Seeded demo student mastery for: {seed_student}")
    except Neo4jGraphRepositoryError:
        raise
    finally:
        neo.close()
        db.close()


if __name__ == "__main__":
    run()
