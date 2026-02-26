"""AI Core Quiz Generation Engine.

This module currently returns deterministic mock data for Section 4 while
keeping the API contract stable for backend integration.
"""

from __future__ import annotations

import uuid
from typing import Any


async def generate_quiz_questions(
    subject: str,
    sss_level: str,
    term: int,
    topic_id: uuid.UUID,
    purpose: str,
    difficulty: str,
    num_questions: int,
) -> list[dict[str, Any]]:
    _ = (sss_level, term, topic_id, purpose)
    questions: list[dict[str, Any]] = []
    for idx in range(num_questions):
        questions.append(
            {
                "id": uuid.uuid4(),
                "text": f"Sample {difficulty} question {idx + 1} about {subject}?",
                "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                "correct_answer": "A",
                "concept_id": str(uuid.uuid4()),
                "difficulty": difficulty,
            }
        )
    return questions


async def generate_quiz_insights(quiz_id: uuid.UUID, attempt_id: uuid.UUID) -> list[str]:
    _ = (quiz_id, attempt_id)
    return [
        "You struggled with concept X; review that section.",
        "You answered quickly on concept Y, showing good mastery.",
    ]
