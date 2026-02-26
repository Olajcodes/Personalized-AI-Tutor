from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status

from backend.schemas.quiz_schema import QuizResultsResponse, ConceptBreakdownItem
from backend.repositories.quiz_repo import QuizRepository
# Hypothetical AI insights client
from backend.core.ai_core_client import generate_quiz_insights

class QuizResultsService:
    def __init__(self, db: Session):
        self.repo = QuizRepository(db)

    async def get_results(self, quiz_id: UUID, student_id: UUID, attempt_id: UUID) -> QuizResultsResponse:
        # 1. Fetch attempt and quiz
        attempt = self.repo.get_attempt_with_answers(attempt_id)
        if not attempt or attempt.quiz_id != quiz_id or attempt.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        quiz = self.repo.get_quiz_with_questions(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        # 2. Build concept breakdown from answers
        questions = self.repo.get_questions_for_quiz(quiz_id)
        question_map = {q.id: q for q in questions}
        concept_map = {}  # concept_id -> list of correctness
        for answer in getattr(attempt, "answers", []):
            q = question_map.get(answer.question_id)
            if q:
                concept_id = getattr(q, "concept_id", q.id)
                if concept_id not in concept_map:
                    concept_map[concept_id] = []
                concept_map[concept_id].append(bool(answer.is_correct))

        concept_breakdown = []
        for concept_id, correctness_list in concept_map.items():
            # Simple average correctness for this concept
            avg_correct = sum(correctness_list) / len(correctness_list)
            concept_breakdown.append(ConceptBreakdownItem(
                concept_id=concept_id,
                correct=avg_correct > 0.5,  # threshold
                mastery_delta=0.0  # not computed here
            ))

        # 3. Get AI insights (mock for now)
        insights = await generate_quiz_insights(quiz_id, attempt_id)

        # 4. Determine recommended revision topic (could be based on weakest concept)
        recommended_topic = None
        if concept_breakdown:
            # Find concept with lowest correctness
            weakest = min(concept_breakdown, key=lambda x: x.correct)
            # Map concept to topic (requires topic-concept mapping – assume external service)
            recommended_topic = await self._get_topic_for_concept(weakest.concept_id)

        return QuizResultsResponse(
            score=attempt.score,
            concept_breakdown=concept_breakdown,
            insights=insights,
            recommended_revision_topic_id=recommended_topic
        )

    async def _get_topic_for_concept(self, concept_id: UUID) -> UUID | None:
        # Placeholder: would query graph or topic-concept mapping table
        return None
