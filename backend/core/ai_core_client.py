from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

import httpx

from backend.core.config import settings

logger = logging.getLogger(__name__)


def _fallback_questions(*, difficulty: str, num_questions: int) -> list[dict[str, Any]]:
    return [
        {
            "id": uuid4(),
            "text": f"Question {idx + 1}",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "concept_id": str(uuid4()),
            "difficulty": difficulty,
        }
        for idx in range(num_questions)
    ]


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
    """Fetch quiz questions from ai-core, falling back to local deterministic data."""
    base_url = settings.ai_core_base_url.rstrip("/")
    if not base_url:
        return _fallback_questions(difficulty=difficulty, num_questions=num_questions)

    payload = {
        "subject": subject,
        "sss_level": sss_level,
        "term": term,
        "topic_id": str(topic_id),
        "purpose": purpose,
        "difficulty": difficulty,
        "num_questions": num_questions,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.ai_core_timeout_seconds) as client:
            response = await client.post(f"{base_url}/quiz/generate", json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("ai-core /quiz/generate failed, using fallback quiz generator: %s", exc)
        return _fallback_questions(difficulty=difficulty, num_questions=num_questions)

    questions = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(questions, list) or not questions:
        logger.warning("ai-core /quiz/generate returned invalid payload, using fallback questions")
        return _fallback_questions(difficulty=difficulty, num_questions=num_questions)

    return questions


async def generate_quiz_insights(quiz_id, attempt_id) -> list[str]:
    """Fetch insight text from ai-core, falling back to a static response."""
    base_url = settings.ai_core_base_url.rstrip("/")
    if not base_url:
        return ["Review foundational concepts before retrying this topic."]

    try:
        async with httpx.AsyncClient(timeout=settings.ai_core_timeout_seconds) as client:
            response = await client.get(f"{base_url}/quiz/{quiz_id}/attempt/{attempt_id}/insights")
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        logger.warning("ai-core insights call failed, using fallback insight: %s", exc)
        return ["Review foundational concepts before retrying this topic."]

    insights = data.get("insights") if isinstance(data, dict) else None
    if isinstance(insights, list) and insights:
        return [str(item) for item in insights]

    return ["Review foundational concepts before retrying this topic."]
