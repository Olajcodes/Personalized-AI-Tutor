from __future__ import annotations

from statistics import mean
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.diagnostic_repo import DiagnosticRepository
from backend.repositories.graph_repo import GraphRepository
from backend.schemas.internal_graph_schema import (
    InternalGraphContextOut,
    InternalGraphUpdateIn,
    InternalGraphUpdateOut,
    MasteryNodeOut,
    PrereqEdgeOut,
)


MASTERY_UNLOCK_THRESHOLD = 0.7


class GraphClientValidationError(ValueError):
    pass


class GraphClientService:
    @staticmethod
    def _topic_concept_id(topic_id) -> str:
        return str(topic_id)

    def get_student_graph_context(
        self,
        db: Session,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        topic_id: str | None = None,
    ) -> InternalGraphContextOut:
        diagnostic_repo = DiagnosticRepository(db)
        if not diagnostic_repo.validate_student_scope(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        ):
            raise GraphClientValidationError(
                "Student scope is invalid. Ensure profile, level, term, and subject enrollment are correct."
            )

        topics = diagnostic_repo.get_scope_topics(subject=subject, sss_level=sss_level, term=term)
        graph_repo = GraphRepository(db)
        mastery_map = graph_repo.get_mastery_map(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        )

        mastery_nodes: list[MasteryNodeOut] = []
        prereq_edges: list[PrereqEdgeOut] = []
        unlocked_nodes: list[str] = []

        for idx, topic in enumerate(topics):
            concept_id = self._topic_concept_id(topic.id)
            score = round(mastery_map.get(concept_id, 0.0), 4)
            mastery_nodes.append(MasteryNodeOut(concept_id=concept_id, score=score))

            if idx > 0:
                prereq_topic = topics[idx - 1]
                prereq_edges.append(
                    PrereqEdgeOut(
                        prerequisite_concept_id=self._topic_concept_id(prereq_topic.id),
                        concept_id=concept_id,
                    )
                )

            if idx == 0:
                unlocked_nodes.append(concept_id)
            else:
                prev_topic = topics[idx - 1]
                prev_score = mastery_map.get(self._topic_concept_id(prev_topic.id), 0.0)
                if prev_score >= MASTERY_UNLOCK_THRESHOLD:
                    unlocked_nodes.append(concept_id)

        overall_mastery = round(mean([node.score for node in mastery_nodes]), 4) if mastery_nodes else 0.0

        return InternalGraphContextOut(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
            mastery=mastery_nodes,
            prereqs=prereq_edges,
            unlocked_nodes=unlocked_nodes,
            overall_mastery=overall_mastery,
        )

    def push_mastery_update(self, db: Session, *, payload: InternalGraphUpdateIn) -> InternalGraphUpdateOut:
        diagnostic_repo = DiagnosticRepository(db)
        if not diagnostic_repo.validate_student_scope(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        ):
            raise GraphClientValidationError(
                "Student scope is invalid. Ensure profile, level, term, and subject enrollment are correct."
            )

        graph_repo = GraphRepository(db)
        mastery_map = graph_repo.get_mastery_map(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )

        event_mastery: list[dict] = []
        for item in payload.concept_breakdown:
            previous = mastery_map.get(item.concept_id, 0.0)
            delta = abs(item.weight_change) if item.is_correct else -abs(item.weight_change)
            projected = previous + delta

            _, stored_new = graph_repo.upsert_mastery(
                student_id=payload.student_id,
                subject=payload.subject,
                sss_level=payload.sss_level,
                term=payload.term,
                concept_id=item.concept_id,
                new_score=projected,
                source=payload.source,
                evaluated_at=payload.timestamp,
            )
            mastery_map[item.concept_id] = stored_new
            event_mastery.append(
                {
                    "concept_id": item.concept_id,
                    "previous_score": round(previous, 4),
                    "new_score": round(stored_new, 4),
                    "delta": round(stored_new - previous, 4),
                }
            )

        graph_repo.record_update_event(
            student_id=payload.student_id,
            quiz_id=payload.quiz_id,
            attempt_id=payload.attempt_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
            source=payload.source,
            concept_breakdown=[item.model_dump() for item in payload.concept_breakdown],
            new_mastery=event_mastery,
        )
        db.commit()

        overall_mastery = round(mean(mastery_map.values()), 4) if mastery_map else 0.0
        return InternalGraphUpdateOut(
            success=True,
            new_mastery=overall_mastery,
            updated_concepts=len(payload.concept_breakdown),
        )


graph_client_service = GraphClientService()

