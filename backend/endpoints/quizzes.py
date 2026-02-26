from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.quiz_schema import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
    QuizResultsResponse,
)
from backend.services.quiz_generate_service import QuizGenerateService
from backend.services.quiz_submit_service import QuizSubmitService
from backend.services.quiz_results_service import QuizResultsService


router = APIRouter(prefix="/learning/quizzes", tags=["Quizzes"])


@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_quiz(
    payload: QuizGenerateRequest,
    db: Session = Depends(get_db),
):
    service = QuizGenerateService(db)
    return await service.generate_quiz(payload)


@router.post(
    "/{quiz_id}/submit",
    response_model=QuizSubmitResponse,
)
async def submit_quiz(
    quiz_id: UUID,
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
):
    service = QuizSubmitService(db)
    return await service.submit_quiz(quiz_id=quiz_id, request=payload)


@router.get(
    "/{quiz_id}/results",
    response_model=QuizResultsResponse,
)
async def get_quiz_results(
    quiz_id: UUID,
    student_id: UUID,
    attempt_id: UUID,
    db: Session = Depends(get_db),
):
    service = QuizResultsService(db)
    return await service.get_results(
        quiz_id=quiz_id,
        student_id=student_id,
        attempt_id=attempt_id,
    )
