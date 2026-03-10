from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import mean
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.diagnostic_repo import DiagnosticRepository
from backend.repositories.graph_repo import GraphRepository
from backend.schemas.graph_learning_schema import (
    GraphConceptEdgeOut,
    GraphConceptNodeOut,
    GraphNextStepOut,
    LessonGraphContextOut,
    WhyThisTopicOut,
)
from backend.schemas.learning_path_schema import PathNextIn
from backend.services.learning_path_service import learning_path_service


MASTERY_THRESHOLD = 0.7


class LessonGraphValidationError(ValueError):
    pass


@dataclass(frozen=True)
class _TopicConcept:
    concept_id: str
    label: str
    topic_id: str | None
    topic_title: str | None


class LessonGraphService:
    @staticmethod
    def _readable_concept_label(concept_id: str, *, fallback_topic_title: str | None = None) -> str:
        value = str(concept_id or "").strip()
        if not value:
            return str(fallback_topic_title or "Untitled Concept").strip()
        try:
            UUID(value)
            fallback = str(fallback_topic_title or "").strip()
            return fallback or "Topic Concept"
        except ValueError:
            pass
        token = value.rsplit(":", 1)[-1].strip().lower()
        token = re.sub(r"-(\d+)$", "", token)
        token = re.sub(r"[_-]+", " ", token)
        token = re.sub(r"\s+", " ", token).strip()
        return token.title() if token else str(fallback_topic_title or "Untitled Concept").strip()

    def _scoped_graph(
        self,
        db: Session,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
    ) -> tuple[dict[str, list[str]], dict[str, _TopicConcept], list[tuple[str, str]], dict[str, float]]:
        diagnostic_repo = DiagnosticRepository(db)
        if not diagnostic_repo.validate_student_scope(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        ):
            raise LessonGraphValidationError(
                "Student scope is invalid. Ensure profile, level, term, and subject enrollment are correct."
            )

        rows = diagnostic_repo.get_scope_topic_concept_rows(subject=subject, sss_level=sss_level, term=term)
        mastery_map = GraphRepository(db).get_mastery_map(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        )

        topic_to_concepts: dict[str, list[str]] = {}
        concept_lookup: dict[str, _TopicConcept] = {}
        prereq_edges: set[tuple[str, str]] = set()
        ordered_concepts: list[str] = []
        seen: set[str] = set()

        for row in rows:
            topic_id = str(row.get("topic_id") or "").strip()
            topic_title = str(row.get("topic_title") or "").strip()
            concept_id = str(row.get("concept_id") or "").strip()
            if not topic_id or not concept_id:
                continue
            topic_to_concepts.setdefault(topic_id, [])
            if concept_id not in topic_to_concepts[topic_id]:
                topic_to_concepts[topic_id].append(concept_id)
            concept_lookup[concept_id] = _TopicConcept(
                concept_id=concept_id,
                label=self._readable_concept_label(concept_id, fallback_topic_title=topic_title),
                topic_id=topic_id,
                topic_title=topic_title,
            )
            if concept_id not in seen:
                seen.add(concept_id)
                ordered_concepts.append(concept_id)
            for prereq_id in [str(value).strip() for value in (row.get("prereq_concept_ids") or []) if str(value).strip()]:
                if prereq_id and prereq_id != concept_id:
                    prereq_edges.add((prereq_id, concept_id))

        if not prereq_edges:
            for index in range(1, len(ordered_concepts)):
                prereq_edges.add((ordered_concepts[index - 1], ordered_concepts[index]))

        return topic_to_concepts, concept_lookup, sorted(prereq_edges), mastery_map

    @staticmethod
    def _unlocked(prereq_edges: list[tuple[str, str]], mastery_map: dict[str, float]) -> set[str]:
        prereq_by_concept: dict[str, set[str]] = {}
        all_nodes: set[str] = set()
        for prereq, concept in prereq_edges:
            all_nodes.add(prereq)
            all_nodes.add(concept)
            prereq_by_concept.setdefault(concept, set()).add(prereq)

        unlocked: set[str] = set()
        for concept_id in all_nodes:
            prereqs = prereq_by_concept.get(concept_id, set())
            if not prereqs or all(mastery_map.get(prereq, 0.0) >= MASTERY_THRESHOLD for prereq in prereqs):
                unlocked.add(concept_id)
        return unlocked

    @staticmethod
    def _node(
        *,
        concept: _TopicConcept,
        mastery_score: float,
        role: str,
        is_unlocked: bool,
    ) -> GraphConceptNodeOut:
        if mastery_score >= MASTERY_THRESHOLD:
            mastery_state = "demonstrated"
        elif mastery_score > 0:
            mastery_state = "needs_review"
        else:
            mastery_state = "unassessed"
        return GraphConceptNodeOut(
            concept_id=concept.concept_id,
            label=concept.label,
            topic_id=concept.topic_id,
            topic_title=concept.topic_title,
            mastery_score=round(float(mastery_score), 4),
            mastery_state=mastery_state,
            role=role,  # type: ignore[arg-type]
            is_unlocked=is_unlocked,
        )

    def get_lesson_graph_context(
        self,
        db: Session,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: UUID,
    ) -> LessonGraphContextOut:
        topic_to_concepts, concept_lookup, prereq_edges, mastery_map = self._scoped_graph(
            db,
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        )
        topic_key = str(topic_id)
        current_ids = list(topic_to_concepts.get(topic_key) or [])
        if not current_ids:
            raise LessonGraphValidationError("Topic is not available in the approved graph scope.")

        def _lookup(concept_id: str) -> _TopicConcept:
            concept = concept_lookup.get(concept_id)
            if concept is not None:
                return concept
            return _TopicConcept(
                concept_id=concept_id,
                label=self._readable_concept_label(concept_id),
                topic_id=None,
                topic_title=None,
            )

        unlocked = self._unlocked(prereq_edges, mastery_map)
        prerequisite_ids = list(
            dict.fromkeys([prereq for prereq, concept in prereq_edges if concept in current_ids])
        )
        downstream_ids = list(
            dict.fromkeys([concept for prereq, concept in prereq_edges if prereq in current_ids])
        )
        related_ids = list(dict.fromkeys(current_ids + prerequisite_ids + downstream_ids))

        current_nodes = [
            self._node(
                concept=_lookup(concept_id),
                mastery_score=mastery_map.get(concept_id, 0.0),
                role="current",
                is_unlocked=concept_id in unlocked,
            )
            for concept_id in current_ids
        ]
        prerequisite_nodes = [
            self._node(
                concept=_lookup(concept_id),
                mastery_score=mastery_map.get(concept_id, 0.0),
                role="prerequisite",
                is_unlocked=concept_id in unlocked,
            )
            for concept_id in prerequisite_ids
        ]
        downstream_nodes = [
            self._node(
                concept=_lookup(concept_id),
                mastery_score=mastery_map.get(concept_id, 0.0),
                role="downstream",
                is_unlocked=concept_id in unlocked,
            )
            for concept_id in downstream_ids
        ]
        weakest_nodes = sorted(current_nodes, key=lambda item: item.mastery_score)[:3]

        graph_nodes = [
            self._node(
                concept=_lookup(concept_id),
                mastery_score=mastery_map.get(concept_id, 0.0),
                role=(
                    "current"
                    if concept_id in current_ids
                    else "prerequisite"
                    if concept_id in prerequisite_ids
                    else "downstream"
                ),
                is_unlocked=concept_id in unlocked,
            )
            for concept_id in related_ids
        ]
        graph_edges = [
            GraphConceptEdgeOut(
                source_concept_id=prereq_id,
                target_concept_id=concept_id,
                relation="PREREQ_OF",
            )
            for prereq_id, concept_id in prereq_edges
            if prereq_id in related_ids and concept_id in related_ids
        ]

        next_step = learning_path_service.calculate_next_step(
            db=db,
            payload=PathNextIn(
                student_id=student_id,
                subject=subject,  # type: ignore[arg-type]
                sss_level=sss_level,  # type: ignore[arg-type]
                term=term,
            ),
        )

        next_unlock = None
        if next_step.recommended_topic_id:
            lead_concept_id = next_step.recommended_concept_id
            lead_concept = _lookup(lead_concept_id) if lead_concept_id else None
            next_unlock = GraphNextStepOut(
                concept_id=lead_concept_id,
                concept_label=(
                    next_step.recommended_concept_label
                    or (lead_concept.label if lead_concept else None)
                ),
                topic_id=next_step.recommended_topic_id,
                topic_title=next_step.recommended_topic_title or (lead_concept.topic_title if lead_concept else None),
                reason=next_step.reason,
            )

        topic_title = current_nodes[0].topic_title or "Current Topic"
        why_this_matters = (
            f"{topic_title} builds on "
            f"{', '.join(node.label for node in prerequisite_nodes[:2]) or 'foundational concepts'} "
            f"and unlocks "
            f"{', '.join(node.label for node in downstream_nodes[:2]) or 'the next concepts in your path'}."
        )
        overall_mastery = round(mean([mastery_map.get(concept_id, 0.0) for concept_id in current_ids]), 4)

        return LessonGraphContextOut(
            student_id=student_id,
            subject=subject,  # type: ignore[arg-type]
            sss_level=sss_level,  # type: ignore[arg-type]
            term=term,
            topic_id=topic_key,
            topic_title=topic_title,
            overall_mastery=overall_mastery,
            current_concepts=current_nodes,
            prerequisite_concepts=prerequisite_nodes,
            downstream_concepts=downstream_nodes,
            weakest_concepts=weakest_nodes,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            next_unlock=next_unlock,
            why_this_matters=why_this_matters,
        )

    def explain_why_this_topic(
        self,
        db: Session,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: UUID,
    ) -> WhyThisTopicOut:
        context = self.get_lesson_graph_context(
            db,
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
        )
        weakest_prereq = min(
            context.prerequisite_concepts,
            key=lambda item: item.mastery_score,
            default=None,
        )
        return WhyThisTopicOut(
            student_id=student_id,
            subject=subject,  # type: ignore[arg-type]
            sss_level=sss_level,  # type: ignore[arg-type]
            term=term,
            topic_id=context.topic_id,
            topic_title=context.topic_title,
            explanation=context.why_this_matters
            or f"{context.topic_title} sits in the path because it bridges prerequisites into later topics.",
            prerequisite_labels=[item.label for item in context.prerequisite_concepts],
            unlock_labels=[item.label for item in context.downstream_concepts],
            weakest_prerequisite_label=weakest_prereq.label if weakest_prereq else None,
            recommended_next=context.next_unlock,
        )


lesson_graph_service = LessonGraphService()
