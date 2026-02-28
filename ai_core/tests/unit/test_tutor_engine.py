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
