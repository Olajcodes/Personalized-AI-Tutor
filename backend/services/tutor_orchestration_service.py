from __future__ import annotations

from typing import Any

import httpx

from backend.core.config import settings
from backend.schemas.tutor_schema import (
    TutorChatIn,
    TutorChatOut,
    TutorExplainMistakeIn,
    TutorExplainMistakeOut,
    TutorHintIn,
    TutorHintOut,
    TutorRecommendationOut,
)


class TutorOrchestrationError(RuntimeError):
    """Base exception for tutor orchestration failures."""


class TutorProviderUnavailableError(TutorOrchestrationError):
    """Raised when ai-core is unavailable and fallback is disabled."""


class TutorProviderContractError(TutorOrchestrationError):
    """Raised when ai-core response violates expected contract."""


class TutorOrchestrationService:
    def __init__(self):
        self.base_url = settings.ai_core_base_url.rstrip("/")
        self.timeout_seconds = max(float(settings.ai_core_timeout_seconds), 1.0)
        self.allow_fallback = bool(settings.ai_core_allow_fallback)

    @staticmethod
    def _fallback_chat(payload: TutorChatIn) -> TutorChatOut:
        recommendation = TutorRecommendationOut(
            type="next_topic",
            topic_id=str(payload.topic_id) if payload.topic_id else None,
            reason="Continue practicing this scope while mastery evidence is still building.",
        )
        return TutorChatOut(
            assistant_message=(
                f"Let's work through this together. For {payload.subject.upper()} ({payload.sss_level}, term {payload.term}), "
                "start by identifying the core rule, then apply it to one simple example."
            ),
            citations=[],
            actions=["UPDATED_MASTERY_BASIC"],
            recommendations=[recommendation],
        )

    @staticmethod
    def _fallback_hint(payload: TutorHintIn) -> TutorHintOut:
        return TutorHintOut(
            hint="Break the question into smaller parts and eliminate clearly wrong options first.",
            strategy="guided_hint",
        )

    @staticmethod
    def _fallback_explain(payload: TutorExplainMistakeIn) -> TutorExplainMistakeOut:
        return TutorExplainMistakeOut(
            explanation=(
                "Your answer likely missed the core rule used in this question. "
                f"The expected answer is '{payload.correct_answer}', while you selected '{payload.student_answer}'."
            ),
            improvement_tip="State the governing rule first, then re-check each option against that rule.",
        )

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.base_url:
            raise TutorProviderUnavailableError("AI_CORE_BASE_URL is not configured.")

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}{path}", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise TutorProviderUnavailableError(f"ai-core request failed: {exc}") from exc

        if not isinstance(data, dict):
            raise TutorProviderContractError("ai-core response must be an object.")
        return data

    async def chat(self, payload: TutorChatIn) -> TutorChatOut:
        request_payload = {
            "student_id": str(payload.student_id),
            "session_id": str(payload.session_id),
            "subject": payload.subject,
            "sss_level": payload.sss_level,
            "term": payload.term,
            "topic_id": str(payload.topic_id) if payload.topic_id else None,
            "message": payload.message,
        }

        try:
            data = await self._post("/tutor/chat", request_payload)
            return TutorChatOut.model_validate(data)
        except (TutorProviderUnavailableError, TutorProviderContractError):
            if not self.allow_fallback:
                raise
            return self._fallback_chat(payload)

    async def hint(self, payload: TutorHintIn) -> TutorHintOut:
        request_payload = {
            "student_id": str(payload.student_id),
            "session_id": str(payload.session_id) if payload.session_id else None,
            "quiz_id": str(payload.quiz_id),
            "question_id": payload.question_id,
            "subject": payload.subject,
            "sss_level": payload.sss_level,
            "term": payload.term,
            "topic_id": str(payload.topic_id) if payload.topic_id else None,
            "message": payload.message,
        }

        try:
            data = await self._post("/tutor/hint", request_payload)
            return TutorHintOut.model_validate(data)
        except (TutorProviderUnavailableError, TutorProviderContractError):
            if not self.allow_fallback:
                raise
            return self._fallback_hint(payload)

    async def explain_mistake(self, payload: TutorExplainMistakeIn) -> TutorExplainMistakeOut:
        request_payload = {
            "student_id": str(payload.student_id),
            "session_id": str(payload.session_id) if payload.session_id else None,
            "subject": payload.subject,
            "sss_level": payload.sss_level,
            "term": payload.term,
            "topic_id": str(payload.topic_id) if payload.topic_id else None,
            "question": payload.question,
            "student_answer": payload.student_answer,
            "correct_answer": payload.correct_answer,
        }

        try:
            data = await self._post("/tutor/explain-mistake", request_payload)
            return TutorExplainMistakeOut.model_validate(data)
        except (TutorProviderUnavailableError, TutorProviderContractError):
            if not self.allow_fallback:
                raise
            return self._fallback_explain(payload)
