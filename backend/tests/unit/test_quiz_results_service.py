import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException

from backend.services.quiz_results_service import QuizResultsService
from backend.models.quiz import QuizAttempt, QuizAnswer, QuizQuestion, Quiz


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def quiz_id():
    return uuid4()


@pytest.fixture
def student_id():
    return uuid4()


@pytest.fixture
def attempt_id():
    return uuid4()


@pytest.fixture
def mock_attempt(attempt_id, quiz_id, student_id):
    attempt = MagicMock(spec=QuizAttempt)
    attempt.id = attempt_id
    attempt.quiz_id = quiz_id
    attempt.student_id = student_id
    attempt.score = 80.0
    attempt.answers = []
    return attempt


@pytest.fixture
def mock_quiz(quiz_id):
    quiz = MagicMock(spec=Quiz)
    quiz.id = quiz_id
    return quiz


@pytest.mark.asyncio
async def test_get_results_success(
    mock_db, quiz_id, student_id, attempt_id, mock_attempt, mock_quiz
):
    service = QuizResultsService(mock_db)
    service.repo.get_attempt_with_answers = MagicMock(return_value=mock_attempt)
    service.repo.get_quiz_with_questions = MagicMock(return_value=mock_quiz)
    service.repo.get_questions_for_quiz = MagicMock(return_value=[])

    with patch(
        "backend.services.quiz_results_service.generate_quiz_insights",
        new=AsyncMock(return_value=["Insight 1"]),
    ):
        response = await service.get_results(quiz_id, student_id, attempt_id)

    assert response.score == 80.0
    assert response.insights == ["Insight 1"]


@pytest.mark.asyncio
async def test_get_results_attempt_not_found(
    mock_db, quiz_id, student_id, attempt_id
):
    service = QuizResultsService(mock_db)
    service.repo.get_attempt_with_answers = MagicMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.get_results(quiz_id, student_id, attempt_id)
    assert exc.value.status_code == 404