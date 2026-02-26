from __future__ import annotations

from typing import Any
from uuid import uuid4


async def generate_quiz_questions(
    *,
    subject: str,
    sss_level: str,
    term: int,
    topic_id,
    purpose: str,
    difficulty: str,
    num_questions: int,
) -> list[dict[str, Any]]:
    """Temporary local stub until ai-core HTTP integration is wired."""
    _ = (subject, sss_level, term, topic_id, purpose, difficulty)
    questions: list[dict[str, Any]] = []
    for idx in range(num_questions):
        questions.append(
            {
                "id": uuid4(),
                "text": f"Question {idx + 1}",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "concept_id": uuid4(),
                "difficulty": difficulty,
            }
        )
    return questions


async def generate_quiz_insights(quiz_id, attempt_id) -> list[str]:
    """Temporary local stub until ai-core HTTP integration is wired."""
    _ = (quiz_id, attempt_id)
    return ["Review foundational concepts before retrying this topic."]
