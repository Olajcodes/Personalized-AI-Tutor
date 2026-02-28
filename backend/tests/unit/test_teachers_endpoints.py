from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.main import app
from backend.services.teacher_service import TeacherServiceConflictError, TeacherServiceUnauthorizedError


def _override_db():
    yield object()


def test_teachers_endpoints_success(monkeypatch):
    teacher_id = uuid4()
    class_id = uuid4()
    student_id = uuid4()

    def _override_user():
        return SimpleNamespace(id=teacher_id, role="teacher")

    class _TeacherService:
        def list_classes(self, *, teacher_id):
            return {
                "classes": [
                    {
                        "id": str(class_id),
                        "teacher_id": str(teacher_id),
                        "name": "SSS2 Math A",
                        "description": None,
                        "subject": "math",
                        "sss_level": "SSS2",
                        "term": 1,
                        "is_active": True,
                        "enrolled_count": 1,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            }

        def create_class(self, *, teacher_id, payload):
            return self.list_classes(teacher_id=teacher_id)["classes"][0]

        def enroll_students(self, *, teacher_id, class_id, payload):
            return {
                "class_id": str(class_id),
                "enrolled_student_ids": [str(student_id)],
                "already_enrolled_student_ids": [],
                "total_enrolled": 1,
            }

        def remove_student_enrollment(self, *, teacher_id, class_id, student_id):
            return True

        def create_assignment(self, *, teacher_id, payload):
            return {
                "id": str(uuid4()),
                "teacher_id": str(teacher_id),
                "class_id": str(payload.class_id) if payload.class_id else None,
                "student_id": str(payload.student_id) if payload.student_id else None,
                "assignment_type": payload.assignment_type,
                "ref_id": payload.ref_id,
                "title": payload.title,
                "instructions": payload.instructions,
                "subject": payload.subject,
                "sss_level": payload.sss_level,
                "term": payload.term,
                "due_at": None,
                "status": "assigned",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        def create_intervention(self, *, teacher_id, payload):
            return {
                "id": str(uuid4()),
                "teacher_id": str(teacher_id),
                "class_id": str(payload.class_id) if payload.class_id else None,
                "student_id": str(payload.student_id),
                "intervention_type": payload.intervention_type,
                "severity": payload.severity,
                "subject": payload.subject,
                "sss_level": payload.sss_level,
                "term": payload.term,
                "notes": payload.notes,
                "action_plan": payload.action_plan,
                "status": "open",
                "resolved_at": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

    class _AnalyticsService:
        def get_class_dashboard(self, *, teacher_id, class_id):
            return {
                "class_id": str(class_id),
                "total_students": 1,
                "active_students_7d": 1,
                "avg_study_time_seconds_7d": 120,
                "avg_mastery_score": 0.5,
                "completion_distribution": {"completed": 1, "in_progress": 0, "no_activity": 0},
            }

        def get_class_heatmap(self, *, teacher_id, class_id):
            return {"class_id": str(class_id), "points": [{"concept_id": "c1", "avg_score": 0.5, "student_count": 1}]}

        def get_class_alerts(self, *, teacher_id, class_id):
            return {"class_id": str(class_id), "alerts": []}

        def get_student_timeline(self, *, teacher_id, class_id, student_id, limit):
            return {"class_id": str(class_id), "student_id": str(student_id), "timeline": []}

    monkeypatch.setattr("backend.endpoints.teachers._teacher_service", lambda db: _TeacherService())
    monkeypatch.setattr("backend.endpoints.teachers._analytics_service", lambda db: _AnalyticsService())

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)

    list_resp = client.get("/api/v1/teachers/classes")
    create_resp = client.post(
        "/api/v1/teachers/classes",
        json={"name": "SSS2 Math A", "description": None, "subject": "math", "sss_level": "SSS2", "term": 1},
    )
    enroll_resp = client.post(
        f"/api/v1/teachers/classes/{class_id}/enroll",
        json={"student_ids": [str(student_id)]},
    )
    dashboard_resp = client.get(f"/api/v1/teachers/classes/{class_id}/dashboard")
    heatmap_resp = client.get(f"/api/v1/teachers/classes/{class_id}/heatmap")
    alerts_resp = client.get(f"/api/v1/teachers/classes/{class_id}/alerts")
    timeline_resp = client.get(f"/api/v1/teachers/classes/{class_id}/students/{student_id}/timeline")
    assignment_resp = client.post(
        "/api/v1/teachers/assignments",
        json={
            "class_id": str(class_id),
            "student_id": str(student_id),
            "assignment_type": "topic",
            "ref_id": "topic-1",
            "title": "Algebra Revision",
            "instructions": "Revise chapter 1",
            "subject": "math",
            "sss_level": "SSS2",
            "term": 1,
            "due_at": None,
        },
    )
    intervention_resp = client.post(
        "/api/v1/teachers/interventions",
        json={
            "class_id": str(class_id),
            "student_id": str(student_id),
            "intervention_type": "note",
            "severity": "medium",
            "subject": "math",
            "sss_level": "SSS2",
            "term": 1,
            "notes": "Needs extra help",
            "action_plan": "Follow-up session",
        },
    )
    delete_resp = client.delete(f"/api/v1/teachers/classes/{class_id}/enroll/{student_id}")

    app.dependency_overrides.clear()

    assert list_resp.status_code == 200
    assert create_resp.status_code == 201
    assert enroll_resp.status_code == 200
    assert dashboard_resp.status_code == 200
    assert heatmap_resp.status_code == 200
    assert alerts_resp.status_code == 200
    assert timeline_resp.status_code == 200
    assert assignment_resp.status_code == 201
    assert intervention_resp.status_code == 201
    assert delete_resp.status_code == 204


def test_teachers_endpoint_error_mapping(monkeypatch):
    teacher_id = uuid4()

    def _override_user():
        return SimpleNamespace(id=teacher_id, role="teacher")

    class _TeacherService:
        def create_class(self, *, teacher_id, payload):
            raise TeacherServiceConflictError("duplicate class")

        def list_classes(self, *, teacher_id):
            raise TeacherServiceUnauthorizedError("forbidden")

    class _AnalyticsService:
        pass

    monkeypatch.setattr("backend.endpoints.teachers._teacher_service", lambda db: _TeacherService())
    monkeypatch.setattr("backend.endpoints.teachers._analytics_service", lambda db: _AnalyticsService())

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    client = TestClient(app)

    list_resp = client.get("/api/v1/teachers/classes")
    create_resp = client.post(
        "/api/v1/teachers/classes",
        json={"name": "SSS1 English", "description": None, "subject": "english", "sss_level": "SSS1", "term": 1},
    )

    app.dependency_overrides.clear()
    assert list_resp.status_code == 403
    assert create_resp.status_code == 409
