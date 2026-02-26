from __future__ import annotations

from sqlalchemy.orm import Session
from uuid import UUID

from backend.repositories.diagnostic_repo import DiagnosticRepository
from backend.repositories.graph_repo import GraphRepository
from backend.schemas.learning_path_schema import (
    LearningMapNodeOut,
    LearningMapVisualOut,
    PathNextIn,
    PathNextOut,
)


MASTERY_THRESHOLD = 0.7


class LearningPathValidationError(ValueError):
    pass


class LearningPathService:
    @staticmethod
    def _topic_concept_id(topic_id) -> str:
        return str(topic_id)

    def calculate_next_step(self, db: Session, payload: PathNextIn) -> PathNextOut:
        diagnostic_repo = DiagnosticRepository(db)
        if not diagnostic_repo.validate_student_scope(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        ):
            raise LearningPathValidationError(
                "Student scope is invalid. Ensure profile, level, term, and subject enrollment are correct."
            )

        topics = diagnostic_repo.get_scope_topics(
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )
        if not topics:
            raise LearningPathValidationError("No approved topics found for the requested scope.")

        mastery_map = GraphRepository(db).get_mastery_map(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
        )

        for idx, topic in enumerate(topics):
            concept_id = self._topic_concept_id(topic.id)
            concept_mastery = mastery_map.get(concept_id, 0.0)
            if concept_mastery >= MASTERY_THRESHOLD:
                continue

            prereq_gaps: list[str] = []
            if idx > 0:
                prereq_topic = topics[idx - 1]
                prereq_concept_id = self._topic_concept_id(prereq_topic.id)
                prereq_mastery = mastery_map.get(prereq_concept_id, 0.0)
                if prereq_mastery < MASTERY_THRESHOLD:
                    prereq_gaps.append(prereq_concept_id)
                    return PathNextOut(
                        recommended_topic_id=str(prereq_topic.id),
                        reason="Prerequisite mastery is below threshold; complete prerequisite topic first.",
                        prereq_gaps=prereq_gaps,
                    )

            return PathNextOut(
                recommended_topic_id=str(topic.id),
                reason="Recommended next topic based on mastery and prerequisite progression.",
                prereq_gaps=prereq_gaps,
            )

        weakest_topic = min(topics, key=lambda t: mastery_map.get(self._topic_concept_id(t.id), 1.0))
        return PathNextOut(
            recommended_topic_id=str(weakest_topic.id),
            reason="All scoped topics are above threshold; recommending weakest topic for revision.",
            prereq_gaps=[],
        )

    def get_learning_map_visual(
        self,
        db: Session,
        *,
        student_id: UUID,
        subject: str,
        sss_level: str,
        term: int,
        view: str,
    ) -> LearningMapVisualOut:
        diagnostic_repo = DiagnosticRepository(db)
        if not diagnostic_repo.validate_student_scope(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        ):
            raise LearningPathValidationError(
                "Student scope is invalid. Ensure profile, level, term, and subject enrollment are correct."
            )

        topics = diagnostic_repo.get_scope_topics(subject=subject, sss_level=sss_level, term=term)
        mastery_map = GraphRepository(db).get_mastery_map(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
        )

        nodes: list[LearningMapNodeOut] = []
        current_assigned = False
        for idx, topic in enumerate(topics):
            concept_id = self._topic_concept_id(topic.id)
            score = round(mastery_map.get(concept_id, 0.0), 4)
            prev_concept_id = self._topic_concept_id(topics[idx - 1].id) if idx > 0 else None
            prev_mastered = idx == 0 or mastery_map.get(prev_concept_id, 0.0) >= MASTERY_THRESHOLD

            if score >= MASTERY_THRESHOLD:
                status = "mastered"
            elif prev_mastered and not current_assigned:
                status = "current"
                current_assigned = True
            elif prev_mastered:
                status = "current"
            else:
                status = "locked"

            nodes.append(
                LearningMapNodeOut(
                    topic_id=str(topic.id),
                    concept_id=concept_id,
                    status=status,
                    mastery_score=score,
                )
            )

        return LearningMapVisualOut(
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            view=view,
            nodes=nodes,
        )


learning_path_service = LearningPathService()
