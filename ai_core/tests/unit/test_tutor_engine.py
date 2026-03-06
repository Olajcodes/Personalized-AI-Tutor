from ai_core.core_engine.api_contracts.schemas import (
    TutorChatRequest,
    TutorExplainMistakeRequest,
    TutorHintRequest,
)
from ai_core.core_engine.orchestration.tutor_engine import (
    run_tutor_chat,
    run_tutor_explain_mistake,
    run_tutor_hint,
)


def test_run_tutor_chat_contract(monkeypatch):
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_profile_context",
        lambda request: {
            "student_id": request.student_id,
            "profile_id": "profile-1",
            "sss_level": request.sss_level,
            "term": request.term,
            "subjects": [request.subject],
            "preferences": {"explanation_depth": "standard", "examples_first": True, "pace": "normal"},
        },
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_history_context",
        lambda request: {"messages": [{"role": "student", "content": "Earlier question"}]},
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_lesson_context",
        lambda request: {
            "student_id": request.student_id,
            "topic_id": request.topic_id,
            "title": "Lesson: Algebra Basics",
            "summary": "Focus on variables and simple equations.",
            "content_blocks": [{"type": "text", "value": "A variable represents an unknown quantity."}],
            "source_chunk_ids": ["chunk-1"],
            "generation_metadata": {"generator_version": "rag_mastery_v1"},
        },
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_graph_context",
        lambda request: {
            "mastery": [{"concept_id": "math:sss2:t1:linear-equations", "score": 0.42}],
            "prereqs": [
                {
                    "prerequisite_concept_id": "math:sss2:t1:variables",
                    "concept_id": "math:sss2:t1:linear-equations",
                }
            ],
            "unlocked_nodes": ["math:sss2:t1:variables"],
            "overall_mastery": 0.42,
        },
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_rag_retrieve",
        lambda request: [],
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._llm_generate",
        lambda prompt: "This is a scoped tutor response.",
    )
    out = run_tutor_chat(
        TutorChatRequest(
            student_id="user-1",
            session_id="session-1",
            subject="math",
            sss_level="SSS2",
            term=1,
            topic_id="topic-1",
            message="Explain algebra basics",
        )
    )
    assert out.assistant_message
    assert isinstance(out.actions, list)
    assert isinstance(out.recommendations, list)
    assert "USED_LESSON_CONTEXT" in out.actions


def test_run_tutor_chat_aborts_when_no_lesson_or_rag_context(monkeypatch):
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_profile_context",
        lambda request: {},
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_history_context",
        lambda request: {"messages": []},
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_lesson_context",
        lambda request: None,
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_graph_context",
        lambda request: {},
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._internal_rag_retrieve",
        lambda request: [],
    )

    out = run_tutor_chat(
        TutorChatRequest(
            student_id="user-1",
            session_id="session-1",
            subject="math",
            sss_level="SSS2",
            term=1,
            topic_id="topic-1",
            message="Explain algebra basics",
        )
    )

    assert "no lesson-aware context found" in out.assistant_message.lower()
    assert "NO_CONTEXT_ABORTED" in out.actions


def test_run_tutor_hint_contract(monkeypatch):
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._llm_generate",
        lambda prompt: "Start by identifying the main rule.",
    )
    out = run_tutor_hint(
        TutorHintRequest(
            student_id="user-1",
            session_id="session-1",
            quiz_id="quiz-1",
            question_id="q1",
            subject="english",
            sss_level="SSS1",
            term=1,
            topic_id=None,
            message="Need hint",
        )
    )
    assert out.hint
    assert out.strategy == "guided_hint"


def test_run_tutor_explain_mistake_contract(monkeypatch):
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.tutor_engine._llm_generate",
        lambda prompt: "You mixed up the branches of government.",
    )
    out = run_tutor_explain_mistake(
        TutorExplainMistakeRequest(
            student_id="user-1",
            session_id="session-1",
            subject="civic",
            sss_level="SSS3",
            term=2,
            topic_id=None,
            question="Who makes laws?",
            student_answer="Judiciary",
            correct_answer="Legislature",
        )
    )
    assert out.explanation
    assert out.improvement_tip
