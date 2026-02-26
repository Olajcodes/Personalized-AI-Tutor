"""Lightweight ai-core HTTP app for container/service health."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI

from ai_core.core_engine.orchestration.quiz_engine import (
    generate_quiz_questions,
    generate_quiz_insights,
)
from ai_core.core_engine.api_contracts.quiz_schemas import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuestionSchema,
)

app = FastAPI(title="Mastery AI Core", version="0.1.0")


@app.get("/")
def root():
    return {"service": "ai-core", "status": "online"}


@app.get("/health")
def health():
    checks = {
        "llm_api_key": "configured" if os.getenv("LLM_API_KEY") else "not_configured",
        "postgres_dsn": "configured" if os.getenv("POSTGRES_DSN") else "not_configured",
        "neo4j_uri": "configured" if os.getenv("NEO4J_URI") else "not_configured",
        "redis_url": "configured" if os.getenv("REDIS_URL") else "not_configured",
        "vector_index_name": "configured" if os.getenv("VECTOR_INDEX_NAME") else "not_configured",
    }
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@app.post("/quiz/generate", response_model=QuizGenerateResponse)
async def quiz_generate(payload: QuizGenerateRequest):
    questions_raw = await generate_quiz_questions(
        subject=payload.subject,
        sss_level=payload.sss_level,
        term=payload.term,
        topic_id=payload.topic_id,
        purpose=payload.purpose,
        difficulty=payload.difficulty,
        num_questions=payload.num_questions,
    )

    # Convert dicts -> Pydantic models
    questions = [QuestionSchema(**q) for q in questions_raw]
    return QuizGenerateResponse(questions=questions)


@app.get("/quiz/{quiz_id}/attempt/{attempt_id}/insights")
async def quiz_insights(quiz_id: UUID, attempt_id: UUID):
    insights = await generate_quiz_insights(quiz_id=quiz_id, attempt_id=attempt_id)
    return {"insights": insights}
