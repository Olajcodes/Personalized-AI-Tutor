from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.auth import get_current_user
from backend.main import app


def _override_user(user_id):
    def _inner():
        return SimpleNamespace(id=user_id, role="student")

    return _inner


def test_course_bootstrap_requires_matching_student_id():
    auth_user_id = uuid4()
    payload_student_id = uuid4()
    client = TestClient(app)
    app.dependency_overrides[get_current_user] = _override_user(auth_user_id)

    response = client.get(
        "/api/v1/learning/course/bootstrap",
        params={
            "student_id": str(payload_student_id),
            "subject": "math",
            "term": 1,
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 403


def test_course_bootstrap_returns_graph_ready_payload(monkeypatch):
    student_id = uuid4()

    monkeypatch.setattr(
        "backend.endpoints.course_learning.CourseExperienceService.bootstrap",
        lambda self, **kwargs: {
            "student_id": str(kwargs["student_id"]),
            "subject": kwargs["subject"],
            "sss_level": "SSS2",
            "term": kwargs["term"],
            "topics": [
                {
                    "topic_id": str(uuid4()),
                    "title": "Sequences and Series",
                    "description": "Graph-backed progression entry.",
                    "lesson_title": "Lesson: Sequences and Series",
                    "estimated_duration_minutes": 24,
                    "lesson_ready": True,
                    "lesson_unavailable_reason": None,
                    "sss_level": "SSS2",
                    "term": kwargs["term"],
                    "subject_id": str(uuid4()),
                    "status": "current",
                    "mastery_score": 0.42,
                    "concept_label": "Arithmetic Progression",
                    "graph_details": "Weakest focus: Arithmetic Progression",
                    "is_recommended": True,
                }
            ],
            "next_step": {
                "recommended_topic_id": str(uuid4()),
                "recommended_topic_title": "Sequences and Series",
                "recommended_concept_id": "math:sss2:t2:arithmetic-progression",
                "recommended_concept_label": "Arithmetic Progression",
                "reason": "Recommended next topic based on the weakest concept still below mastery threshold.",
                "prereq_gaps": [],
                "prereq_gap_labels": [],
                "scope_warning": None,
                "unmapped_topic_titles": [],
            },
            "recent_evidence": {
                "source": "practice",
                "created_at": "2026-03-12T10:00:00Z",
                "strongest_gain_concept_label": "Arithmetic Progression",
                "strongest_drop_concept_label": "Simple Interest",
                "summary": "Latest practice strengthened Arithmetic Progression but exposed a gap in Simple Interest.",
            },
            "map_error": None,
            "warmed_topic_ids": [],
            "cache_hit_topic_ids": [],
            "failed_topic_ids": [],
        },
    )

    client = TestClient(app)
    app.dependency_overrides[get_current_user] = _override_user(student_id)

    response = client.get(
        "/api/v1/learning/course/bootstrap",
        params={
            "student_id": str(student_id),
            "subject": "math",
            "term": 2,
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["subject"] == "math"
    assert body["topics"][0]["status"] == "current"
    assert body["topics"][0]["concept_label"] == "Arithmetic Progression"
    assert body["next_step"]["recommended_concept_label"] == "Arithmetic Progression"
    assert body["recent_evidence"]["strongest_drop_concept_label"] == "Simple Interest"
