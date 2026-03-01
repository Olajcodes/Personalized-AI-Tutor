import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base, get_db
from backend.main import app
from backend.models.user import User


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "").strip()
if not TEST_DATABASE_URL:
    pytest.skip(
        "Section 8 E2E teacher flow requires TEST_DATABASE_URL (PostgreSQL).",
        allow_module_level=True,
    )

if not TEST_DATABASE_URL.startswith("postgresql"):
    pytest.skip(
        "Section 8 E2E teacher flow requires PostgreSQL TEST_DATABASE_URL.",
        allow_module_level=True,
    )


engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield

    cleanup = TestingSessionLocal()
    cleanup.query(User).filter(
        User.email.like("e2e.teacher.%@example.com")
        | User.email.like("e2e.class.student.%@example.com")
    ).delete(synchronize_session=False)
    cleanup.commit()
    cleanup.close()
    app.dependency_overrides.clear()


def _register_and_login(client: TestClient, *, role: str, email_prefix: str) -> tuple[str, str]:
    email = f"{email_prefix}.{uuid4()}@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": role,
            "first_name": "Test",
            "last_name": role.capitalize(),
            "display_name": f"Test {role.capitalize()}",
        },
    )
    assert register.status_code == 201
    user_id = register.json()["user_id"]

    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return user_id, token


def test_e2e_teacher_flow():
    client = TestClient(app)

    teacher_id, teacher_token = _register_and_login(client, role="teacher", email_prefix="e2e.teacher")
    student_id, _ = _register_and_login(client, role="student", email_prefix="e2e.class.student")
    headers = {"Authorization": f"Bearer {teacher_token}"}

    create_class = client.post(
        "/api/v1/teachers/classes",
        json={
            "name": f"E2E Teacher Class {str(uuid4())[:8]}",
            "description": "E2E teacher flow class",
            "subject": "math",
            "sss_level": "SSS2",
            "term": 1,
        },
        headers=headers,
    )
    assert create_class.status_code == 201
    class_id = create_class.json()["id"]

    enroll = client.post(
        f"/api/v1/teachers/classes/{class_id}/enroll",
        json={"student_ids": [student_id]},
        headers=headers,
    )
    assert enroll.status_code == 200
    assert student_id in [str(item) for item in enroll.json()["enrolled_student_ids"]]

    class_list = client.get("/api/v1/teachers/classes", headers=headers)
    assert class_list.status_code == 200
    assert any(item["id"] == class_id for item in class_list.json()["classes"])

    roster = client.get("/api/v1/internal/postgres/class-roster", params={"class_id": class_id})
    assert roster.status_code == 200
    assert student_id in [str(item) for item in roster.json()["student_ids"]]

    dashboard = client.get(f"/api/v1/teachers/classes/{class_id}/dashboard", headers=headers)
    assert dashboard.status_code == 200

    heatmap = client.get(f"/api/v1/teachers/classes/{class_id}/heatmap", headers=headers)
    assert heatmap.status_code == 200

    alerts = client.get(f"/api/v1/teachers/classes/{class_id}/alerts", headers=headers)
    assert alerts.status_code == 200

    timeline = client.get(
        f"/api/v1/teachers/classes/{class_id}/students/{student_id}/timeline",
        headers=headers,
    )
    assert timeline.status_code == 200

    assignment = client.post(
        "/api/v1/teachers/assignments",
        json={
            "class_id": class_id,
            "student_id": student_id,
            "assignment_type": "topic",
            "ref_id": "linear-equations",
            "title": "Linear Equations Assignment",
            "instructions": "Solve 10 practice questions.",
            "subject": "math",
            "sss_level": "SSS2",
            "term": 1,
        },
        headers=headers,
    )
    assert assignment.status_code == 201

    intervention = client.post(
        "/api/v1/teachers/interventions",
        json={
            "class_id": class_id,
            "student_id": student_id,
            "intervention_type": "note",
            "severity": "medium",
            "subject": "math",
            "sss_level": "SSS2",
            "term": 1,
            "notes": "Needs extra support with equation balancing.",
            "action_plan": "Schedule a short one-on-one remediation.",
        },
        headers=headers,
    )
    assert intervention.status_code == 201

    remove = client.delete(
        f"/api/v1/teachers/classes/{class_id}/enroll/{student_id}",
        headers=headers,
    )
    assert remove.status_code == 204

    # sanity check teacher identity in token-linked route
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == teacher_id
