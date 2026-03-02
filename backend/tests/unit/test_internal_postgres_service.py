import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.schemas.internal_postgres_schema import InternalQuizAnswerIn, InternalQuizAttemptIn
from backend.services.internal_postgres_service import (
    InternalPostgresService,
    InternalProfileNotFoundError,
)


class FakeInternalPostgresRepo:
    def __init__(self):
        self.profile_context = None
        self.history_rows = []
        self.saved_payload = None
        self.save_row = None
        self.roster = []

    def get_profile_context(self, *, student_id):
        _ = student_id
        return self.profile_context

    def get_history(self, *, student_id, session_id):
        _ = (student_id, session_id)
        return self.history_rows

    def save_quiz_attempt(self, payload):
        self.saved_payload = payload
        return self.save_row

    def get_class_roster(self, *, class_id):
        _ = class_id
        return self.roster


def test_get_profile_raises_when_missing():
    repo = FakeInternalPostgresRepo()
    service = InternalPostgresService(repo)

    with pytest.raises(InternalProfileNotFoundError, match="Student profile not found"):
        service.get_profile(uuid4())


def test_get_profile_success_maps_response():
    repo = FakeInternalPostgresRepo()
    service = InternalPostgresService(repo)
    student_id = uuid4()
    profile_id = uuid4()
    repo.profile_context = {
        "student_id": student_id,
        "profile_id": profile_id,
        "sss_level": "SSS2",
        "term": 2,
        "subjects": ["math", "english"],
        "preferences": {"explanation_depth": "standard", "examples_first": True, "pace": "normal"},
    }

    out = service.get_profile(student_id)

    assert out.student_id == student_id
    assert out.profile_id == profile_id
    assert out.sss_level == "SSS2"
    assert out.term == 2
    assert out.subjects == ["math", "english"]


def test_get_history_success_maps_messages():
    repo = FakeInternalPostgresRepo()
    service = InternalPostgresService(repo)
    student_id = uuid4()
    session_id = uuid4()
    repo.history_rows = [
        {"id": uuid4(), "role": "student", "content": "hi", "created_at": datetime.now(timezone.utc)},
        {"id": uuid4(), "role": "assistant", "content": "hello", "created_at": datetime.now(timezone.utc)},
    ]

    out = service.get_history(student_id=student_id, session_id=session_id)

    assert out.student_id == student_id
    assert out.session_id == session_id
    assert len(out.messages) == 2
    assert out.messages[1].role == "assistant"


def test_store_quiz_attempt_success_and_serialization():
    repo = FakeInternalPostgresRepo()
    service = InternalPostgresService(repo)
    attempt_id = uuid4()
    created_at = datetime.now(timezone.utc)
    repo.save_row = {"attempt_id": attempt_id, "created_at": created_at}

    payload = InternalQuizAttemptIn(
        student_id=uuid4(),
        quiz_id=uuid4(),
        subject="math",
        sss_level="SSS1",
        term=1,
        answers=[InternalQuizAnswerIn(question_id="q1", answer="B")],
        time_taken_seconds=120,
        score=80,
    )

    out = service.store_quiz_attempt(payload)

    assert out.attempt_id == attempt_id
    assert out.stored is True
    answers = json.loads(repo.saved_payload["answers_json"])
    assert answers[0]["question_id"] == "q1"
    assert answers[0]["answer"] == "B"


def test_store_quiz_attempt_failure_raises():
    repo = FakeInternalPostgresRepo()
    service = InternalPostgresService(repo)
    repo.save_row = {}

    payload = InternalQuizAttemptIn(
        student_id=uuid4(),
        quiz_id=uuid4(),
        subject="civic",
        sss_level="SSS3",
        term=3,
        answers=[InternalQuizAnswerIn(question_id="q2", answer="A")],
        time_taken_seconds=50,
        score=60,
    )

    with pytest.raises(RuntimeError, match="Failed to store quiz attempt"):
        service.store_quiz_attempt(payload)


def test_get_class_roster_returns_ids():
    repo = FakeInternalPostgresRepo()
    service = InternalPostgresService(repo)
    class_id = uuid4()
    repo.roster = [uuid4(), uuid4()]

    out = service.get_class_roster(class_id)

    assert out.class_id == class_id
    assert len(out.student_ids) == 2
