import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from backend.main import app
from backend.core.database import Base, get_db
from backend.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from backend.models.subject import Subject
from backend.core.config import settings

# Use an in-memory SQLite database for integration tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if engine.dialect.name == "sqlite":
    pytest.skip(
        "Section 4 integration flow requires a Postgres-compatible JSONB test database.",
        allow_module_level=True,
    )


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    # Seed subjects (required for foreign key constraints)
    db = TestingSessionLocal()
    if not db.query(Subject).first():
        subjects = [
            Subject(id=uuid4(), slug="math", name="Mathematics"),
            Subject(id=uuid4(), slug="english", name="English"),
            Subject(id=uuid4(), slug="civic", name="Civic"),
        ]
        db.add_all(subjects)
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def test_full_quiz_flow():
    # Step 1: Generate quiz
    student_id = uuid4()
    topic_id = uuid4()
    generate_payload = {
        "student_id": str(student_id),
        "subject": "math",
        "sss_level": "SSS2",
        "term": 1,
        "topic_id": str(topic_id),
        "purpose": "practice",
        "difficulty": "medium",
        "num_questions": 2,
    }
    gen_response = client.post("/api/v1/learning/quizzes/generate", json=generate_payload)
    assert gen_response.status_code == 200
    gen_data = gen_response.json()
    quiz_id = gen_data["quiz_id"]
    questions = gen_data["questions"]
    assert len(questions) == 2

    # Step 2: Submit quiz
    submit_payload = {
        "student_id": str(student_id),
        "answers": [
            {"question_id": questions[0]["id"], "answer": "A"},
            {"question_id": questions[1]["id"], "answer": "B"},
        ],
        "time_taken_seconds": 180,
    }
    submit_response = client.post(f"/api/v1/learning/quizzes/{quiz_id}/submit", json=submit_payload)
    assert submit_response.status_code == 200
    submit_data = submit_response.json()
    attempt_id = submit_data["attempt_id"]
    assert "score" in submit_data

    # Step 3: Get results
    results_response = client.get(
        f"/api/v1/learning/quizzes/{quiz_id}/results",
        params={"student_id": str(student_id), "attempt_id": attempt_id},
    )
    assert results_response.status_code == 200
    results_data = results_response.json()
    assert "score" in results_data
    assert "concept_breakdown" in results_data
    assert "insights" in results_data
