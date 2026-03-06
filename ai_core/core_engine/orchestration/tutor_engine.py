"""Tutor orchestration utilities.

Includes:
- legacy single-call orchestration (`handle_question`)
- section-5 aligned helpers for HTTP tutor endpoints (`run_tutor_chat`, `run_tutor_hint`, `run_tutor_explain_mistake`)
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING
from uuid import UUID

import requests

from ai_core.core_engine.api_contracts.schemas import (
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
from ai_core.core_engine.llm.client import LLMClient, LLMClientError
from ai_core.core_engine.observability.logging import get_logger
from ai_core.core_engine.safety.injection import sanitize_user_text
from ai_core.core_engine.safety.moderation import ModerationError, basic_moderate

if TYPE_CHECKING:
    from ai_core.core_engine.config.settings import Settings
    from ai_core.core_engine.curriculum.resolver import CurriculumResolver
    from ai_core.core_engine.knowledge_graph.prerequisites import PrereqService
    from ai_core.core_engine.llm.client import LLMClient
    from ai_core.core_engine.mastery.updater import MasteryUpdater
    from ai_core.core_engine.observability.cost import CostTracker
    from ai_core.core_engine.rag.retriever import RagRetriever

logger = get_logger(__name__)


def _sanitize_and_moderate(text: str, *, max_chars: int = 6000) -> str:
    cleaned = sanitize_user_text((text or "")[:max_chars])
    basic_moderate(cleaned)
    return cleaned


def _normalize_rag_query(raw: str) -> str | None:
    normalized = " ".join((raw or "").split())
    if len(normalized) < 3:
        return None
    return normalized[:4000]


def _normalize_topic_ids(topic_id: str | None) -> list[str]:
    if not topic_id:
        return []
    try:
        UUID(str(topic_id))
    except (TypeError, ValueError):
        logger.warning("tutor._internal_rag_retrieve skipping invalid topic_id: %s", topic_id)
        return []
    return [str(topic_id)]


def _request_json(
    method: str,
    url: str,
    *,
    params: dict | None = None,
    payload: dict | None = None,
    timeout: float,
) -> dict:
    response = requests.request(method, url, params=params, json=payload, timeout=timeout)
    if not response.ok:
        detail = (response.text or "").strip()
        raise RuntimeError(
            f"internal request failed ({response.status_code}): {detail[:500] or 'no response body'}"
        )
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("internal request returned a non-object payload")
    return data


def _internal_postgres_base_url() -> str:
    return os.getenv("BACKEND_INTERNAL_POSTGRES_URL", "http://127.0.0.1:8000/api/v1/internal/postgres").strip().rstrip("/")


def _internal_graph_context_url() -> str:
    return os.getenv(
        "BACKEND_INTERNAL_GRAPH_CONTEXT_URL",
        "http://127.0.0.1:8000/api/v1/internal/graph/context",
    ).strip()


def _internal_context_timeout() -> float:
    return float(os.getenv("INTERNAL_CONTEXT_TIMEOUT_SECONDS", "5"))


def _internal_profile_context(request: TutorChatRequest) -> dict:
    return _request_json(
        "GET",
        f"{_internal_postgres_base_url()}/profile",
        params={"student_id": request.student_id},
        timeout=_internal_context_timeout(),
    )


def _internal_history_context(request: TutorChatRequest) -> dict:
    return _request_json(
        "GET",
        f"{_internal_postgres_base_url()}/history",
        params={"student_id": request.student_id, "session_id": request.session_id},
        timeout=_internal_context_timeout(),
    )


def _internal_lesson_context(request: TutorChatRequest) -> dict | None:
    if not request.topic_id:
        return None
    return _request_json(
        "GET",
        f"{_internal_postgres_base_url()}/lesson-context",
        params={"student_id": request.student_id, "topic_id": request.topic_id},
        timeout=_internal_context_timeout(),
    )


def _internal_graph_context(request: TutorChatRequest) -> dict:
    params = {
        "student_id": request.student_id,
        "subject": request.subject,
        "sss_level": request.sss_level,
        "term": int(request.term),
    }
    if request.topic_id:
        params["topic_id"] = request.topic_id
    return _request_json(
        "GET",
        _internal_graph_context_url(),
        params=params,
        timeout=_internal_context_timeout(),
    )


def _internal_rag_retrieve(request: TutorChatRequest) -> list[Citation]:
    base_url = os.getenv("BACKEND_INTERNAL_RAG_URL", "http://127.0.0.1:8000/api/v1/internal/rag/retrieve").strip()
    timeout = float(os.getenv("INTERNAL_RAG_TIMEOUT_SECONDS", "6"))
    top_k = int(os.getenv("INTERNAL_RAG_TOP_K", "6"))
    query = _normalize_rag_query(request.message)
    if query is None:
        return []

    payload = {
        "query": query,
        "subject": request.subject,
        "sss_level": request.sss_level,
        "term": int(request.term),
        "topic_ids": _normalize_topic_ids(request.topic_id),
        "top_k": max(1, min(top_k, 20)),
        "approved_only": True,
    }
    allow_scope_fallback = os.getenv("TUTOR_CHAT_ALLOW_SCOPE_FALLBACK", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    def _request_chunks(request_payload: dict) -> list[dict]:
        response = requests.post(base_url, json=request_payload, timeout=timeout)
        if not response.ok:
            detail = (response.text or "").strip()
            raise RuntimeError(
                f"internal RAG request failed ({response.status_code}): {detail[:500] or 'no response body'}"
            )
        data = response.json()
        return list(data.get("chunks", []))

    chunks = _request_chunks(payload)
    if allow_scope_fallback and not chunks and payload["topic_ids"]:
        fallback_payload = dict(payload)
        fallback_payload["topic_ids"] = []
        logger.info(
            "tutor._internal_rag_retrieve empty topic-scoped result; retrying scope-only retrieval",
            extra={
                "subject": request.subject,
                "sss_level": request.sss_level,
                "term": int(request.term),
                "topic_id": request.topic_id,
            },
        )
        chunks = _request_chunks(fallback_payload)

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


def _readable_concept_label(concept_id: str) -> str:
    value = str(concept_id or "").strip()
    if not value:
        return "unknown concept"
    try:
        UUID(value)
        return value
    except ValueError:
        pass
    token = value.rsplit(":", 1)[-1].strip().lower()
    token = re.sub(r"-(\d+)$", "", token)
    token = re.sub(r"[^a-z0-9]+", " ", token).strip()
    return token or value


def _lesson_context_available(lesson_context: dict | None) -> bool:
    if not lesson_context:
        return False
    if str(lesson_context.get("summary") or "").strip():
        return True
    blocks = lesson_context.get("content_blocks")
    return isinstance(blocks, list) and bool(blocks)


def _lesson_context_block_lines(lesson_context: dict | None, *, max_blocks: int = 5) -> list[str]:
    if not lesson_context:
        return []

    rendered: list[str] = []
    for block in list(lesson_context.get("content_blocks") or [])[:max_blocks]:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "text").strip().lower()
        value = block.get("value")
        if isinstance(value, str):
            text = " ".join(value.split()).strip()
        elif isinstance(value, dict):
            parts = [
                " ".join(str(value.get(key) or "").split()).strip()
                for key in ("prompt", "note", "solution", "question", "expected_answer")
            ]
            text = " | ".join(part for part in parts if part)
        else:
            text = ""
        if text:
            rendered.append(f"- {block_type}: {text[:320]}")
    return rendered


def _history_context_lines(history_context: dict | None, *, max_messages: int = 6) -> list[str]:
    if not history_context:
        return []
    rows = list(history_context.get("messages") or [])[-max_messages:]
    rendered: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "message").strip().lower()
        content = " ".join(str(row.get("content") or "").split()).strip()
        if content:
            rendered.append(f"- {role}: {content[:220]}")
    return rendered


def _graph_context_lines(graph_context: dict | None) -> list[str]:
    if not graph_context:
        return []

    mastery_rows = list(graph_context.get("mastery") or [])
    weak_rows = sorted(
        [
            row for row in mastery_rows
            if isinstance(row, dict) and isinstance(row.get("score"), (int, float))
        ],
        key=lambda row: float(row.get("score", 0.0)),
    )[:5]
    weak_summary = ", ".join(
        f"{_readable_concept_label(str(row.get('concept_id') or ''))} ({float(row.get('score', 0.0)):.2f})"
        for row in weak_rows
    )

    prereq_rows = list(graph_context.get("prereqs") or [])[:5]
    prereq_summary = ", ".join(
        (
            f"{_readable_concept_label(str(row.get('prerequisite_concept_id') or ''))}"
            f" -> {_readable_concept_label(str(row.get('concept_id') or ''))}"
        )
        for row in prereq_rows
        if isinstance(row, dict)
    )

    lines = [
        f"- overall_mastery: {float(graph_context.get('overall_mastery') or 0.0):.2f}",
        f"- unlocked_nodes: {len(list(graph_context.get('unlocked_nodes') or []))}",
    ]
    if weak_summary:
        lines.append(f"- weak_concepts: {weak_summary}")
    if prereq_summary:
        lines.append(f"- prerequisite_edges: {prereq_summary}")
    return lines


def _profile_context_lines(profile_context: dict | None) -> list[str]:
    if not profile_context:
        return []
    preferences = profile_context.get("preferences") or {}
    lines = [
        f"- enrolled_subjects: {', '.join(str(item) for item in list(profile_context.get('subjects') or []))}",
        f"- preferred_explanation_depth: {preferences.get('explanation_depth', 'unknown')}",
        f"- examples_first: {bool(preferences.get('examples_first', False))}",
        f"- pace: {preferences.get('pace', 'unknown')}",
    ]
    return lines


def _chat_prompt(
    request: TutorChatRequest,
    *,
    citations: list[Citation],
    profile_context: dict | None,
    history_context: dict | None,
    lesson_context: dict | None,
    graph_context: dict | None,
) -> str:
    if citations:
        citations_block = "\n".join(
            f"- ({item.source_id}#{item.chunk_id}) {item.snippet}" for item in citations
        )
    else:
        citations_block = "- No verified curriculum context retrieved."

    lesson_lines = _lesson_context_block_lines(lesson_context)
    lesson_block = "\n".join(lesson_lines) if lesson_lines else "- No persisted lesson body available."
    history_block = "\n".join(_history_context_lines(history_context)) or "- No prior tutor history."
    graph_block = "\n".join(_graph_context_lines(graph_context)) or "- No graph/mastery context available."
    profile_block = "\n".join(_profile_context_lines(profile_context)) or "- No profile preferences available."
    lesson_title = str((lesson_context or {}).get("title") or "").strip() or "No persisted lesson title"
    lesson_summary = str((lesson_context or {}).get("summary") or "").strip() or "No persisted lesson summary."

    return (
        "You are Mastery AI, a lesson-aware curriculum-bound tutor for Nigerian SSS learners.\n"
        f"Scope: subject={request.subject}, level={request.sss_level}, term={request.term}.\n"
        "Hard constraints:\n"
        "- Do not answer outside this exact scope (subject, level, and term).\n"
        "- Treat the persisted current lesson as the primary context when it is available.\n"
        "- Use retrieved curriculum chunks as supporting evidence and cite source/chunk IDs when possible.\n"
        "- Personalize scaffolding using the mastery/graph context and profile preferences when available.\n"
        "- Do not fabricate facts, sources, or curriculum claims.\n"
        "- If context is insufficient, say what is missing and ask one focused follow-up question.\n"
        "- Keep explanation concise, stepwise, and student-friendly.\n"
        "- Stay inside the currently selected lesson topic unless the student explicitly asks to broaden the scope.\n"
        "- For unsafe requests, refuse and redirect to safe learning support.\n\n"
        f"Current lesson title: {lesson_title}\n"
        f"Current lesson summary: {lesson_summary}\n"
        f"Current lesson body:\n{lesson_block}\n\n"
        f"Student profile and preferences:\n{profile_block}\n\n"
        f"Recent tutor history:\n{history_block}\n\n"
        f"Mastery / graph context:\n{graph_block}\n\n"
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

    from ai_core.core_engine.llm.prompts import build_tutor_prompt
    from ai_core.core_engine.rag.citations import format_citations
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
    profile_context: dict | None = None
    history_context: dict | None = None
    lesson_context: dict | None = None
    graph_context: dict | None = None
    actions: list[str] = ["ENFORCED_SCOPE_POLICY"]

    actions.append("CALLED_TOOL:internal_postgres.profile")
    try:
        profile_context = _internal_profile_context(request)
    except Exception as exc:
        logger.warning("tutor.run_tutor_chat profile fetch failed: %s", exc)
        actions.append("PROFILE_CONTEXT_FAILED")
    else:
        actions.append("USED_PROFILE_CONTEXT")

    actions.append("CALLED_TOOL:internal_postgres.history")
    try:
        history_context = _internal_history_context(request)
    except Exception as exc:
        logger.warning("tutor.run_tutor_chat history fetch failed: %s", exc)
        actions.append("SESSION_HISTORY_FAILED")
    else:
        actions.append("USED_SESSION_HISTORY")

    if request.topic_id:
        actions.append("CALLED_TOOL:internal_postgres.lesson_context")
        try:
            lesson_context = _internal_lesson_context(request)
        except Exception as exc:
            logger.warning("tutor.run_tutor_chat lesson-context fetch failed: %s", exc)
            actions.append("LESSON_CONTEXT_FAILED")
        else:
            actions.append("USED_LESSON_CONTEXT" if _lesson_context_available(lesson_context) else "LESSON_CONTEXT_EMPTY")

    actions.append("CALLED_TOOL:internal_graph.context")
    try:
        graph_context = _internal_graph_context(request)
    except Exception as exc:
        logger.warning("tutor.run_tutor_chat graph-context fetch failed: %s", exc)
        actions.append("GRAPH_CONTEXT_FAILED")
    else:
        actions.append("USED_GRAPH_CONTEXT")

    actions.append("CALLED_TOOL:internal_rag.retrieve")
    try:
        citations = _internal_rag_retrieve(request)
    except Exception as exc:
        detail = str(exc) or "unknown retrieval error"
        logger.warning("tutor.run_tutor_chat retrieval failed: %s", detail)
        actions.append("RAG_RETRIEVAL_FAILED")
    else:
        actions.append("USED_RAG_CONTEXT" if citations else "NO_RAG_CONTEXT")

    if not citations and not _lesson_context_available(lesson_context):
        topic_part = f", topic_id={request.topic_id}" if request.topic_id else ""
        return TutorChatResponse(
            assistant_message=(
                "Tutor unavailable: no lesson-aware context found for "
                f"subject={request.subject}, level={request.sss_level}, term={request.term}{topic_part}. "
                "Generate the lesson successfully and ensure approved curriculum chunks exist for this scope/topic."
            ),
            citations=[],
            actions=actions + ["NO_CONTEXT_ABORTED"],
            recommendations=[],
        )

    prompt = _chat_prompt(
        request,
        citations=citations,
        profile_context=profile_context,
        history_context=history_context,
        lesson_context=lesson_context,
        graph_context=graph_context,
    )
    try:
        assistant_message = _llm_generate(prompt)
    except (LLMClientError, Exception) as exc:
        detail = str(exc) or "unknown model error"
        logger.warning("tutor.run_tutor_chat llm generation failed: %s", detail)
        return TutorChatResponse(
            assistant_message=f"Tutor unavailable: model generation failed: {detail}",
            citations=citations,
            actions=actions + ["LLM_UNAVAILABLE"],
            recommendations=[],
        )

    recommendation = TutorRecommendation(
        type="next_topic",
        topic_id=request.topic_id,
        reason="Stay on the current lesson and close the weakest gaps before moving to a new topic.",
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
