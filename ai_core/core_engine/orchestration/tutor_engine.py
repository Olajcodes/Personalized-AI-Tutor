"""Tutor orchestration utilities.

Includes:
- legacy single-call orchestration (`handle_question`)
- section-5 aligned helpers for HTTP tutor endpoints (`run_tutor_chat`, `run_tutor_hint`, `run_tutor_explain_mistake`)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
from core_engine.observability.logging import get_logger

if TYPE_CHECKING:
    from core_engine.config.settings import Settings
    from core_engine.curriculum.resolver import CurriculumResolver
    from core_engine.knowledge_graph.prerequisites import PrereqService
    from core_engine.llm.client import LLMClient
    from core_engine.mastery.updater import MasteryUpdater
    from core_engine.observability.cost import CostTracker
    from core_engine.rag.retriever import RagRetriever

logger = get_logger(__name__)


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
    from core_engine.safety.injection import sanitize_user_text
    from core_engine.safety.moderation import basic_moderate

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
    """Generate deterministic tutor chat output aligned to section-5 contract.

    This lightweight implementation is safe for MVP integration and can be replaced
    with full LangGraph orchestration without changing API payload shape.
    """
    recommendation = TutorRecommendation(
        type="next_topic",
        topic_id=request.topic_id,
        reason="Keep practicing the current scope and proceed once confidence improves.",
    )
    return TutorChatResponse(
        assistant_message=(
            f"For {request.subject.upper()} ({request.sss_level}, term {request.term}), "
            "start from the core rule, then solve one simple example step by step."
        ),
        citations=[],
        actions=["UPDATED_MASTERY_BASIC"],
        recommendations=[recommendation],
    )


def run_tutor_hint(request: TutorHintRequest) -> TutorHintResponse:
    """Return a concise scaffolded hint for an in-progress quiz question."""
    return TutorHintResponse(
        hint="Identify the key concept being tested, eliminate one wrong option, then compare the remaining choices.",
        strategy="guided_hint",
    )


def run_tutor_explain_mistake(request: TutorExplainMistakeRequest) -> TutorExplainMistakeResponse:
    """Explain why an answer is wrong and provide a targeted correction tip."""
    return TutorExplainMistakeResponse(
        explanation=(
            "Your answer does not follow the governing rule in the question context. "
            f"You selected '{request.student_answer}', but the expected answer is '{request.correct_answer}'."
        ),
        improvement_tip="Write the relevant rule first, then verify each option against that rule.",
    )
