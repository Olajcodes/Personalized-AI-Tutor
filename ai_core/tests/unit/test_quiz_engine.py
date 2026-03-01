import pytest
import uuid
from ai_core.core_engine.orchestration.quiz_engine import (
    generate_quiz_questions,
    generate_quiz_insights,
)


@pytest.mark.anyio
async def test_generate_quiz_questions_returns_correct_structure():
    subject = "math"
    sss_level = "SSS2"
    term = 1
    topic_id = uuid.uuid4()
    purpose = "practice"
    difficulty = "medium"
    num_questions = 3

    questions = await generate_quiz_questions(
        student_id=uuid.uuid4(),
        subject=subject,
        sss_level=sss_level,
        term=term,
        topic_id=topic_id,
        purpose=purpose,
        difficulty=difficulty,
        num_questions=num_questions,
    )

    assert isinstance(questions, list)
    assert len(questions) == num_questions
    for q in questions:
        assert "id" in q
        assert "text" in q
        assert "options" in q
        assert "correct_answer" in q
        assert "concept_id" in q
        assert "difficulty" in q
        assert q["difficulty"] == difficulty


@pytest.mark.anyio
async def test_generate_quiz_insights_returns_list():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    insights = await generate_quiz_insights(quiz_id, attempt_id)
    assert isinstance(insights, list)
    assert len(insights) > 0
