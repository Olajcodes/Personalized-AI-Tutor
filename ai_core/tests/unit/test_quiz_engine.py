import uuid

import pytest

from ai_core.core_engine.orchestration.quiz_engine import (
    QuizGenerationError,
    generate_quiz_insights,
    generate_quiz_questions,
)


@pytest.mark.anyio
async def test_generate_quiz_questions_returns_grounded_structure(monkeypatch):
    topic_id = uuid.uuid4()
    student_id = uuid.uuid4()

    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._internal_lesson_context",
        lambda **kwargs: {
            "student_id": str(student_id),
            "topic_id": str(topic_id),
            "title": "Lesson: Bearings and Distances",
            "summary": "Use three-figure bearings and distance relationships correctly.",
            "content_blocks": [
                {"type": "text", "value": "A bearing is measured clockwise from north."},
                {"type": "example", "value": {"prompt": "Find the bearing", "solution": "Measure clockwise from north."}},
            ],
            "covered_concept_ids": [
                "math:sss1:t2:three-figure-bearings",
                "math:sss1:t2:distance-scale",
            ],
            "covered_concept_labels": {
                "math:sss1:t2:three-figure-bearings": "three figure bearings",
                "math:sss1:t2:distance-scale": "distance scale",
            },
        },
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._internal_rag_context",
        lambda **kwargs: [
            {
                "chunk_id": "chunk-1",
                "source_id": "src-1",
                "text": "A bearing is measured clockwise from north and written using three digits.",
                "metadata": {
                    "concept_id": "math:sss1:t2:three-figure-bearings",
                    "citation_concept_label": "three figure bearings",
                    "citation_topic_title": "Bearings and Distances",
                },
            }
        ],
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._llm_generate",
        lambda prompt: """
        {
          "questions": [
            {
              "text": "A ship sails on a bearing of 045 degrees from a port. What does 045 degrees mean?",
              "options": [
                "45 degrees anticlockwise from north",
                "45 degrees clockwise from north",
                "45 degrees clockwise from east",
                "45 degrees anticlockwise from east"
              ],
              "correct_answer": "B",
              "concept_id": "math:sss1:t2:three-figure-bearings",
              "difficulty": "medium",
              "explanation": "Bearings are measured clockwise from north and written using three digits."
            },
            {
              "text": "On a map drawn to scale, which idea helps you convert a measured map distance to the real distance?",
              "options": [
                "Three figure bearing",
                "Distance scale",
                "Order of operations",
                "Probability"
              ],
              "correct_answer": "B",
              "concept_id": "math:sss1:t2:distance-scale",
              "difficulty": "medium",
              "explanation": "A distance scale links a map measurement to the real-life distance."
            }
          ]
        }
        """,
    )

    questions = await generate_quiz_questions(
        student_id=student_id,
        subject="math",
        sss_level="SSS1",
        term=2,
        topic_id=topic_id,
        purpose="practice",
        difficulty="medium",
        num_questions=2,
    )

    assert len(questions) == 2
    assert questions[0]["correct_answer"] in {"A", "B", "C", "D"}
    assert questions[0]["concept_id"] == "math:sss1:t2:three-figure-bearings"
    assert len(questions[0]["options"]) == 4
    assert questions[0]["explanation"]


@pytest.mark.anyio
async def test_generate_quiz_questions_rejects_placeholder_output(monkeypatch):
    topic_id = uuid.uuid4()
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._internal_lesson_context",
        lambda **kwargs: {
            "title": "Lesson: Bearings and Distances",
            "content_blocks": [{"type": "text", "value": "A bearing is measured clockwise from north."}],
            "covered_concept_ids": ["math:sss1:t2:three-figure-bearings"],
            "covered_concept_labels": {"math:sss1:t2:three-figure-bearings": "three figure bearings"},
        },
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._internal_rag_context",
        lambda **kwargs: [
            {
                "chunk_id": "chunk-1",
                "source_id": "src-1",
                "text": "A bearing is measured clockwise from north.",
                "metadata": {"concept_id": "math:sss1:t2:three-figure-bearings"},
            }
        ],
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._llm_generate",
        lambda prompt: """
        {
          "questions": [
            {
              "text": "Which option best demonstrates understanding of math:sss1:t2:three figure bearings?",
              "options": [
                "A clear example of three figure bearings",
                "An unrelated fact from another topic",
                "A partially correct but incomplete statement",
                "A common misconception students make"
              ],
              "correct_answer": "A",
              "concept_id": "math:sss1:t2:three-figure-bearings",
              "difficulty": "medium",
              "explanation": "placeholder"
            }
          ]
        }
        """,
    )

    with pytest.raises(QuizGenerationError, match="placeholder"):
        await generate_quiz_questions(
            student_id=uuid.uuid4(),
            subject="math",
            sss_level="SSS1",
            term=2,
            topic_id=topic_id,
            purpose="practice",
            difficulty="medium",
            num_questions=1,
        )


@pytest.mark.anyio
async def test_generate_quiz_questions_fails_without_context(monkeypatch):
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._internal_lesson_context",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "ai_core.core_engine.orchestration.quiz_engine._internal_rag_context",
        lambda **kwargs: [],
    )

    with pytest.raises(QuizGenerationError, match="No approved curriculum context"):
        await generate_quiz_questions(
            student_id=uuid.uuid4(),
            subject="math",
            sss_level="SSS1",
            term=2,
            topic_id=uuid.uuid4(),
            purpose="practice",
            difficulty="medium",
            num_questions=1,
        )


@pytest.mark.anyio
async def test_generate_quiz_insights_returns_list():
    quiz_id = uuid.uuid4()
    attempt_id = uuid.uuid4()
    insights = await generate_quiz_insights(quiz_id, attempt_id)
    assert isinstance(insights, list)
    assert len(insights) > 0
