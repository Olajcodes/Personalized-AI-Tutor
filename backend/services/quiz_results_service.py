from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.core.ai_core_client import generate_quiz_insights
from backend.repositories.quiz_repo import QuizRepository
from backend.schemas.quiz_schema import ConceptBreakdownItem, QuizResultsResponse


class QuizResultsService:
    def __init__(self, db: Session):
        self.repo = QuizRepository(db)

    async def get_results(self, quiz_id: UUID, student_id: UUID, attempt_id: UUID) -> QuizResultsResponse:
        attempt = self.repo.get_attempt_with_answers(attempt_id)
        if not attempt or attempt.quiz_id != quiz_id or attempt.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        quiz = self.repo.get_quiz_with_questions(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        questions = self.repo.get_questions_for_quiz(quiz_id)
        question_map = {q.id: q for q in questions}

        concept_correctness: dict[str, list[bool]] = {}
        for answer in getattr(attempt, "answers", []):
            question = question_map.get(answer.question_id)
            if not question:
                continue

            concept_id = str(getattr(question, "concept_id", "")).strip()
            if not concept_id:
                concept_id = str(quiz.topic_id or question.id)
            concept_correctness.setdefault(concept_id, []).append(bool(answer.is_correct))

        concept_breakdown: list[ConceptBreakdownItem] = []
        weakest_concept: str | None = None
        weakest_accuracy = 1.0

        for concept_id, values in concept_correctness.items():
            accuracy = sum(values) / len(values)
            is_correct = accuracy >= 0.5
            weight_change = 0.15 if is_correct else -0.05

            concept_breakdown.append(
                ConceptBreakdownItem(
                    concept_id=concept_id,
                    is_correct=is_correct,
                    weight_change=weight_change,
                )
            )

            if accuracy < weakest_accuracy:
                weakest_accuracy = accuracy
                weakest_concept = concept_id

        try:
            insights = await generate_quiz_insights(quiz_id, attempt_id)
        except Exception:
            insights = ["Insights are temporarily unavailable. Review missed concepts and retry."]

        recommended_topic = None
        if weakest_concept is not None:
            recommended_topic = await self._get_topic_for_concept(weakest_concept, fallback_topic_id=quiz.topic_id)

        return QuizResultsResponse(
            score=float(attempt.score or 0.0),
            concept_breakdown=concept_breakdown,
            insights=insights,
            recommended_revision_topic_id=recommended_topic,
        )

    async def _get_topic_for_concept(self, concept_id: str, fallback_topic_id: UUID | None) -> UUID | None:
        def _parse_uuid(value: str) -> UUID | None:
            try:
                return UUID(value)
            except (TypeError, ValueError):
                return None

        candidates: list[UUID] = []
        direct = _parse_uuid(concept_id)
        if direct is not None:
            candidates.append(direct)

        if concept_id.startswith("topic:"):
            parts = concept_id.split(":")
            if len(parts) >= 2:
                parsed = _parse_uuid(parts[1])
                if parsed is not None:
                    candidates.append(parsed)

        if fallback_topic_id is not None:
            candidates.append(fallback_topic_id)

        for topic_id in candidates:
            if self.repo.topic_exists(topic_id):
                return topic_id

        return None
