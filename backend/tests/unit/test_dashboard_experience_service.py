from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from backend.services.dashboard_experience_service import DashboardExperienceService


def test_dashboard_bootstrap_uses_cache_and_invalidation(monkeypatch):
    student_id = uuid4()
    service = DashboardExperienceService(db=SimpleNamespace())
    profile = SimpleNamespace(
        updated_at=datetime.now(timezone.utc),
        sss_level="SSS2",
        active_term=2,
    )
    calls = {"course": 0}

    monkeypatch.setattr(
        service,
        "_profile_and_subjects",
        lambda **kwargs: (profile, ["english", "math"]),
    )
    monkeypatch.setattr(
        service.course_service,
        "latest_intervention_bootstrap",
        lambda **kwargs: None,
    )

    def _bootstrap(**kwargs):
        calls["course"] += 1
        return {
            "student_id": str(student_id),
            "subject": "english",
            "sss_level": "SSS2",
            "term": 2,
            "topics": [],
            "nodes": [],
            "edges": [],
            "next_step": None,
            "recent_evidence": None,
            "intervention_timeline": [],
            "recommendation_story": None,
            "map_error": None,
            "warmed_topic_ids": [],
            "cache_hit_topic_ids": [],
            "failed_topic_ids": [],
        }

    monkeypatch.setattr(service.course_service, "bootstrap", _bootstrap)

    first = service.bootstrap(student_id=student_id, subject="english")
    second = service.bootstrap(student_id=student_id, subject="english")

    assert calls["course"] == 1
    assert first.active_subject == "english"
    assert second.active_subject == "english"

    DashboardExperienceService.invalidate_student_cache(student_id=student_id)
    third = service.bootstrap(student_id=student_id, subject="english")

    assert calls["course"] == 2
    assert third.active_subject == "english"
