from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.core.ai_core_client import (
    AICoreContractError,
    AICoreProviderError,
    AICoreUnavailableError,
    generate_quiz_questions,
)
from backend.repositories.quiz_repo import QuizRepository
from backend.schemas.quiz_schema import QuestionSchema, QuizGenerateRequest, QuizGenerateResponse

_PLACEHOLDER_MARKERS = (
    "which option best demonstrates understanding of",
    "a common misconception students make",
    "an unrelated fact from another topic",
    "a partially correct but incomplete statement",
    "a clear example of",
)


def _looks_placeholder_question(question: dict) -> bool:
    text = str(question.get("text") or question.get("question_text") or "").strip().lower()
    if any(marker in text for marker in _PLACEHOLDER_MARKERS):
        return True
    if "math:sss" in text or "english:sss" in text or "civic:sss" in text:
        return True

    options = question.get("options") or []
    for option in options:
        lowered = str(option or "").strip().lower()
        if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
            return True
        if "math:sss" in lowered or "english:sss" in lowered or "civic:sss" in lowered:
            return True
    return False


class QuizGenerateService:
    def __init__(self, db: Session):
        self.repo = QuizRepository(db)

    async def generate_quiz(self, request: QuizGenerateRequest) -> QuizGenerateResponse:
        try:
            questions_data = await generate_quiz_questions(
                student_id=request.student_id,
                subject=request.subject,
                sss_level=request.sss_level,
                term=request.term,
                topic_id=request.topic_id,
                purpose=request.purpose,
                difficulty=request.difficulty,
                num_questions=request.num_questions,
            )
        except AICoreContractError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI generation contract error: {exc}",
            ) from exc
        except (AICoreProviderError, AICoreUnavailableError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI generation failed: {exc}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI generation failed: {exc}",
            ) from exc

        if not questions_data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI generation returned no questions",
            )
        if any(_looks_placeholder_question(question) for question in questions_data):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI generation returned low-quality placeholder quiz content",
            )

        quiz = self.repo.create_quiz(
            student_id=request.student_id,
            subject=request.subject,
            sss_level=request.sss_level,
            term=request.term,
            topic_id=request.topic_id,
            purpose=request.purpose,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
        )

        response_questions: list[QuestionSchema] = []
        try:
            for idx, question in enumerate(questions_data):
                question_payload = {
                    "id": question.get("id"),
                    "text": question.get("text") or question.get("question_text"),
                    "options": question.get("options") or [],
                    "correct_answer": question.get("correct_answer"),
                    "concept_id": question.get("concept_id") or str(request.topic_id),
                    "explanation": question.get("explanation"),
                    "topic_id": request.topic_id,
                    "order": idx,
                }
                created_question = self.repo.add_question_to_quiz(quiz.id, question_payload)

                response_questions.append(
                    QuestionSchema(
                        id=created_question.id,
                        text=question_payload["text"],
                        options=question_payload["options"],
                        correct_answer=question_payload["correct_answer"],
                        concept_id=created_question.concept_id,
                        difficulty=question.get("difficulty") or request.difficulty,
                    )
                )
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise

        return QuizGenerateResponse(quiz_id=quiz.id, questions=response_questions)
