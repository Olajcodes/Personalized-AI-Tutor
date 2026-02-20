"""Single entrypoint for MVP tutoring: handle_question()."""

from __future__ import annotations

from core_engine.api_contracts.schemas import TutorRequest, TutorResponse, Citation
from core_engine.config.settings import Settings
from core_engine.curriculum.resolver import CurriculumResolver
from core_engine.rag.retriever import RagRetriever
from core_engine.rag.citations import format_citations
from core_engine.knowledge_graph.prerequisites import PrereqService
from core_engine.llm.client import LLMClient
from core_engine.llm.prompts import build_tutor_prompt
from core_engine.mastery.updater import MasteryUpdater
from core_engine.safety.moderation import basic_moderate
from core_engine.safety.injection import sanitize_user_text
from core_engine.observability.logging import get_logger
from core_engine.observability.cost import CostTracker

logger = get_logger(__name__)


def handle_question(
    request: TutorRequest,
    *,
    settings: Settings,
    curriculum: CurriculumResolver,
    retriever: RagRetriever,
    prereqs: PrereqService,
    llm: LLMClient,
    mastery: MasteryUpdater,
    cost_tracker: CostTracker,
) -> TutorResponse:
    """MVP orchestration:
    resolve scope → retrieve chunks → prereq hints → LLM response → mastery update → logs/cost
    """

    # 1) Safety and hygiene
    user_text = request.message[: settings.max_input_chars]
    user_text = sanitize_user_text(user_text)
    if settings.enable_basic_moderation:
        basic_moderate(user_text)

    # 2) Curriculum scoping
    scope = curriculum.resolve_scope(
        subject_id=request.subject_id,
        jss_level=request.jss_level,
        term=int(request.term),
        topic_id=request.topic_id,
    )

    # 3) RAG retrieval with strict filters
    chunks = retriever.retrieve(
        query=user_text,
        subject_id=scope.subject_id,
        jss_level=scope.jss_level,
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
        jss_level=request.jss_level,
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
            "jss_level": request.jss_level,
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
