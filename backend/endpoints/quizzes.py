from uuid import UUID

from fastapi import APIRouter, Depends, status

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
from backend.core.auth import get_current_user


router = APIRouter(prefix="/api/v1/quizzes", tags=["Quizzes"])


@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_quiz(
    payload: QuizGenerateRequest,
    current_user=Depends(get_current_user),
):
    service = QuizGenerateService()
    return service.generate_quiz(student_id=current_user.id, payload=payload)


@router.post(
    "/{quiz_id}/submit",
    response_model=QuizSubmitResponse,
)
def submit_quiz(
    quiz_id: UUID,
    payload: QuizSubmitRequest,
    current_user=Depends(get_current_user),
):
    service = QuizSubmitService()
    return service.submit_quiz(
        student_id=current_user.id,
        quiz_id=quiz_id,
        payload=payload,
    )


@router.get(
    "/{quiz_id}/results",
    response_model=QuizResultsResponse,
)
def get_quiz_results(
    quiz_id: UUID,
    current_user=Depends(get_current_user),
):
    service = QuizResultsService()
    return service.get_results(
        student_id=current_user.id,
        quiz_id=quiz_id,
    )