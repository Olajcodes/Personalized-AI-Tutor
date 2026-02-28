"""Seed Neo4j with Topic/Concept nodes and prerequisite chain from Postgres topics.

Usage:
  python -m backend.scripts.seed_neo4j_graph

Optional env:
  NEO4J_SEED_STUDENT_ID=<uuid>  # seeds starter HAS_MASTERY links for demo student
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.subject import Subject
from backend.models.topic import Topic
from backend.models.lesson import Lesson  # noqa: F401  # ensure Topic<->Lesson mapper resolves
from backend.repositories.neo4j_graph_repo import (
    Neo4jGraphConfig,
    Neo4jGraphRepository,
    Neo4jGraphRepositoryError,
)


def _group_scope_topics(db: Session) -> dict[tuple[str, str, int], list[Topic]]:
    rows = (
        db.query(Topic, Subject.slug)
        .join(Subject, Subject.id == Topic.subject_id)
        .filter(Topic.is_approved.is_(True))
        .order_by(Subject.slug.asc(), Topic.sss_level.asc(), Topic.term.asc(), Topic.created_at.asc(), Topic.title.asc())
        .all()
    )
    grouped: dict[tuple[str, str, int], list[Topic]] = defaultdict(list)
    for topic, subject_slug in rows:
        grouped[(str(subject_slug), str(topic.sss_level), int(topic.term))].append(topic)
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
    seeded_concepts = 0
    try:
        # Remove legacy relationship type after naming update (MAPS_TO -> COVERS).
        neo.remove_legacy_maps_to_edges()

        grouped = _group_scope_topics(db)
        for (subject, sss_level, term), topics in grouped.items():
            concept_ids = [str(topic.id) for topic in topics]
            neo.ensure_topic_concepts(
                subject=subject,
                sss_level=sss_level,
                term=term,
                topic_ids=concept_ids,
            )
            neo.ensure_prerequisite_chain(concept_ids=concept_ids)
            seeded_scopes += 1
            seeded_concepts += len(concept_ids)

        seed_student = os.getenv("NEO4J_SEED_STUDENT_ID", "").strip()
        if seed_student:
            student_uuid = str(UUID(seed_student))
            first_per_scope = []
            for (_, _, _), topics in grouped.items():
                if topics:
                    first_per_scope.append(str(topics[0].id))
            if first_per_scope:
                # Give starter mastery to first concept in each scope for demo visualizations.
                for concept_id in first_per_scope:
                    neo.upsert_mastery(
                        student_id=student_uuid,
                        concept_id=concept_id,
                        score=0.2,
                        source="seed",
                        evaluated_at=datetime.utcnow(),
                    )

        print(f"Neo4j seed complete. scopes={seeded_scopes}, concepts={seeded_concepts}")
        if seed_student:
            print(f"Seeded demo student mastery for: {seed_student}")
    except Neo4jGraphRepositoryError:
        raise
    finally:
        neo.close()
        db.close()


if __name__ == "__main__":
    run()
