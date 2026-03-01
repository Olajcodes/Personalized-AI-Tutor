"""Tutor orchestration utilities.

Includes:
- legacy single-call orchestration (`handle_question`)
- section-5 aligned helpers for HTTP tutor endpoints (`run_tutor_chat`, `run_tutor_hint`, `run_tutor_explain_mistake`)
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import requests

from core_engine.api_contracts.schemas import (
    Citation,
    TutorChatRequest,
    TutorChatResponse,
    TutorExplainMistakeRequest,
    TutorExplainMistakeResponse,
    TutorHintRequest,
    TutorHintResponse,
    TutorRecommendation,
    TutorRequest,
    TutorResponse,
)
from core_engine.llm.client import LLMClient, LLMClientError
from core_engine.observability.logging import get_logger
from core_engine.safety.injection import sanitize_user_text
from core_engine.safety.moderation import ModerationError, basic_moderate

if TYPE_CHECKING:
    from core_engine.config.settings import Settings
    from core_engine.curriculum.resolver import CurriculumResolver
    from core_engine.knowledge_graph.prerequisites import PrereqService
    from core_engine.llm.client import LLMClient
    from core_engine.mastery.updater import MasteryUpdater
    from core_engine.observability.cost import CostTracker
    from core_engine.rag.retriever import RagRetriever

logger = get_logger(__name__)


def _sanitize_and_moderate(text: str, *, max_chars: int = 6000) -> str:
    cleaned = sanitize_user_text((text or "")[:max_chars])
    basic_moderate(cleaned)
    return cleaned


def _internal_rag_retrieve(request: TutorChatRequest) -> list[Citation]:
    base_url = os.getenv("BACKEND_INTERNAL_RAG_URL", "http://127.0.0.1:8000/api/v1/internal/rag/retrieve").strip()
    timeout = float(os.getenv("INTERNAL_RAG_TIMEOUT_SECONDS", "6"))
    top_k = int(os.getenv("INTERNAL_RAG_TOP_K", "6"))

    payload = {
        "query": request.message,
        "subject": request.subject,
        "sss_level": request.sss_level,
        "term": int(request.term),
        "topic_ids": [request.topic_id] if request.topic_id else [],
        "top_k": max(1, min(top_k, 20)),
        "approved_only": True,
    }

    response = requests.post(base_url, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    chunks = data.get("chunks", [])

    citations: list[Citation] = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        snippet = " ".join(text.split())[:220]
        citations.append(
            Citation(
                source_id=str(chunk.get("source_id") or ""),
                chunk_id=str(chunk.get("chunk_id") or ""),
                snippet=snippet,
                metadata=dict(chunk.get("metadata") or {}),
            )
        )
    return citations


def _llm_generate(prompt: str) -> str:
    client = LLMClient(
        provider=os.getenv("LLM_PROVIDER", "groq"),
        model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
        api_key=os.getenv("LLM_API_KEY"),
    )
    return client.generate(prompt)


def _chat_prompt(request: TutorChatRequest, citations: list[Citation]) -> str:
    if citations:
        citations_block = "\n".join(
            f"- ({item.source_id}#{item.chunk_id}) {item.snippet}" for item in citations
        )
    else:
        citations_block = "- No verified curriculum context retrieved."

    return (
        "You are Mastery AI, a curriculum-bound tutor for Nigerian SSS learners.\n"
        f"Scope: subject={request.subject}, level={request.sss_level}, term={request.term}.\n"
        "Hard constraints:\n"
        "- Do not answer outside this exact scope (subject, level, and term).\n"
        "- Do not fabricate facts, sources, or curriculum claims.\n"
        "- Use retrieved context as primary evidence and cite source/chunk IDs when possible.\n"
        "- If context is insufficient, say what is missing and ask one focused follow-up question.\n"
        "- Keep explanation concise, stepwise, and student-friendly.\n"
        "- For unsafe requests, refuse and redirect to safe learning support.\n\n"
        f"Student question: {request.message}\n\n"
        f"Retrieved context:\n{citations_block}\n"
    )


def handle_question(
    request: TutorRequest,
    *,
    settings: "Settings",
    curriculum: "CurriculumResolver",
    retriever: "RagRetriever",
    prereqs: "PrereqService",
    llm: "LLMClient",
    mastery: "MasteryUpdater",
    cost_tracker: "CostTracker",
) -> TutorResponse:
    """MVP orchestration:
    resolve scope -> retrieve chunks -> prereq hints -> LLM response -> mastery update -> logs/cost
    """

    from core_engine.llm.prompts import build_tutor_prompt
    from core_engine.rag.citations import format_citations
    # 1) Safety and hygiene
    user_text = request.message[: settings.max_input_chars]
    user_text = sanitize_user_text(user_text)
    if settings.enable_basic_moderation:
        basic_moderate(user_text)

    # 2) Curriculum scoping
    scope = curriculum.resolve_scope(
        subject_id=request.subject_id,
        sss_level=request.sss_level,
        term=int(request.term),
        topic_id=request.topic_id,
    )

    # 3) RAG retrieval with strict filters
    chunks = retriever.retrieve(
        query=user_text,
        subject_id=scope.subject_id,
        sss_level=scope.sss_level,
        term=scope.term,
        allowed_topic_ids=scope.allowed_topic_ids,
        approved_only=True,
        top_k=6,
    )
    citations = format_citations(chunks)

    # 4) Optional prerequisite chain
    remediation_prereqs = []
    if request.topic_id:
        remediation_prereqs = prereqs.get_prerequisites_for_topic(topic_id=request.topic_id)

    # 5) LLM prompt + generation
    prompt = build_tutor_prompt(
        user_message=user_text,
        mode=request.mode,
        sss_level=request.sss_level,
        term=int(request.term),
        citations=citations,
        remediation_prereqs=remediation_prereqs,
    )
    with cost_tracker.track(request_id=request.session_id or "single"):
        assistant_text = llm.generate(prompt)

    # 6) Minimal mastery update (only on practice for MVP)
    actions = []
    if request.mode == "practice" and request.topic_id:
        mastery.update_from_interaction(
            user_id=request.user_id,
            subject_id=request.subject_id,
            topic_id=request.topic_id,
            interaction_type="practice",
            signal={"message": user_text},
        )
        actions.append("UPDATED_MASTERY_BASIC")

    # 7) Logs
    logger.info(
        "tutor.handle_question",
        extra={
            "user_id": request.user_id,
            "subject_id": request.subject_id,
            "sss_level": request.sss_level,
            "term": int(request.term),
            "topic_id": request.topic_id,
            "mode": request.mode,
            "rag_chunks": len(chunks),
        },
    )

    return TutorResponse(
        assistant_message=assistant_text,
        citations=[Citation(**c) for c in citations],
        remediation_prereqs=remediation_prereqs,
        actions=actions,
        cost=cost_tracker.snapshot(),
    )


def run_tutor_chat(request: TutorChatRequest) -> TutorChatResponse:
    """Run agentic tutor chat flow using retrieval tool + LLM generation."""
    try:
        safe_message = _sanitize_and_moderate(request.message)
    except ModerationError:
        return TutorChatResponse(
            assistant_message=(
                "I can't help with that request. "
                "Please ask a curriculum-based study question for your selected scope."
            ),
            citations=[],
            actions=["REFUSED_SAFETY_POLICY"],
            recommendations=[],
        )

    request = request.model_copy(update={"message": safe_message})
    citations: list[Citation] = []
    actions: list[str] = ["ENFORCED_SCOPE_POLICY", "CALLED_TOOL:internal_rag.retrieve"]

    try:
        citations = _internal_rag_retrieve(request)
    except Exception as exc:
        logger.warning("tutor.run_tutor_chat retrieval failed: %s", exc)
        actions.append("RAG_RETRIEVAL_FAILED")
    else:
        actions.append("USED_RAG_CONTEXT" if citations else "NO_RAG_CONTEXT")

    prompt = _chat_prompt(request, citations)
    try:
        assistant_message = _llm_generate(prompt)
    except (LLMClientError, Exception) as exc:
        logger.warning("tutor.run_tutor_chat llm generation failed: %s", exc)
        assistant_message = (
            "I could not reach the model right now. "
            "Please retry in a moment, or ask for a short hint while we reconnect."
        )
        actions.append("LLM_UNAVAILABLE")

    recommendation = TutorRecommendation(
        type="next_topic",
        topic_id=request.topic_id,
        reason="Continue in the current topic until accuracy and speed improve consistently.",
    )
    return TutorChatResponse(
        assistant_message=assistant_message,
        citations=citations,
        actions=actions + ["UPDATED_MASTERY_BASIC"],
        recommendations=[recommendation],
    )


def run_tutor_hint(request: TutorHintRequest) -> TutorHintResponse:
    """Return a concise scaffolded hint for an in-progress quiz question."""
    try:
        safe_note = _sanitize_and_moderate(request.message or "")
    except ModerationError:
        return TutorHintResponse(
            hint="I cannot assist with that request. Ask a safe, curriculum-focused question.",
            strategy="policy_refusal",
        )

    prompt = (
        "You are an exam coach. Give a short guided hint only, no full answer.\n"
        f"Scope: {request.subject}, {request.sss_level}, term {request.term}.\n"
        f"Question ID: {request.question_id}\n"
        f"Student note: {safe_note}\n"
    )
    try:
        hint_text = _llm_generate(prompt)
    except (LLMClientError, Exception):
        hint_text = "Focus on the core rule, eliminate one wrong option, then compare the remaining choices."
    return TutorHintResponse(hint=hint_text, strategy="guided_hint")


def run_tutor_explain_mistake(request: TutorExplainMistakeRequest) -> TutorExplainMistakeResponse:
    """Explain why an answer is wrong and provide a targeted correction tip."""
    try:
        safe_question = _sanitize_and_moderate(request.question)
        safe_student_answer = _sanitize_and_moderate(request.student_answer, max_chars=500)
        safe_correct_answer = _sanitize_and_moderate(request.correct_answer, max_chars=500)
    except ModerationError:
        return TutorExplainMistakeResponse(
            explanation="I cannot process that content. Please submit a safe curriculum question.",
            improvement_tip="Rephrase your question using neutral academic language.",
        )

    prompt = (
        "Explain the student's mistake briefly and give one improvement tip.\n"
        f"Scope: {request.subject}, {request.sss_level}, term {request.term}.\n"
        f"Question: {safe_question}\n"
        f"Student answer: {safe_student_answer}\n"
        f"Correct answer: {safe_correct_answer}\n"
    )
    try:
        explanation = _llm_generate(prompt)
    except (LLMClientError, Exception):
        explanation = (
            "Your answer did not follow the governing rule in this question. "
            f"You selected '{request.student_answer}' while the correct answer is '{request.correct_answer}'."
        )
    return TutorExplainMistakeResponse(
        explanation=explanation,
        improvement_tip="Write the relevant rule first, then verify each option against that rule.",
    )
