from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.schemas.teacher_schema import (
    TeacherAssignmentCreateIn,
    TeacherClassCreateIn,
    TeacherClassEnrollIn,
    TeacherInterventionCreateIn,
)
from backend.services.teacher_service import (
    TeacherService,
    TeacherServiceNotFoundError,
    TeacherServiceUnauthorizedError,
    TeacherServiceValidationError,
)


class FakeTeacherRepo:
    def __init__(self):
        self.teacher_id = uuid4()
        self.class_id = uuid4()
        self.student_id = uuid4()
        self.users = {
            self.teacher_id: SimpleNamespace(id=self.teacher_id, role="teacher", is_active=True),
            self.student_id: SimpleNamespace(id=self.student_id, role="student", is_active=True),
        }
        self.teacher_class = SimpleNamespace(
            id=self.class_id,
            teacher_id=self.teacher_id,
            name="SSS2 Math A",
            description=None,
            subject="math",
            sss_level="SSS2",
            term=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.active_students = {self.student_id}

    def get_user(self, user_id):
        return self.users.get(user_id)

    def get_users_by_ids(self, user_ids):
        return {user_id: self.users[user_id] for user_id in user_ids if user_id in self.users}

    def get_teacher_class(self, *, teacher_id, class_id):
        if teacher_id == self.teacher_id and class_id == self.class_id:
            return self.teacher_class
        return None

    def list_teacher_classes(self, *, teacher_id):
        if teacher_id != self.teacher_id:
            return []
        return [(self.teacher_class, len(self.active_students))]

    def create_class(self, **kwargs):
        return self.teacher_class

    def upsert_enrollments(self, *, class_id, student_ids):
        enrolled = []
        already = []
        for student_id in student_ids:
            if student_id in self.active_students:
                already.append(student_id)
            else:
                self.active_students.add(student_id)
                enrolled.append(student_id)
        return enrolled, already

    def count_active_enrollments(self, *, class_id):
        return len(self.active_students)

    def remove_enrollment(self, *, class_id, student_id):
        if student_id in self.active_students:
            self.active_students.remove(student_id)
            return True
        return False

    def get_active_student_ids(self, *, class_id):
        return list(self.active_students)

    def create_assignment(self, payload):
        return SimpleNamespace(
            id=uuid4(),
            teacher_id=payload["teacher_id"],
            class_id=payload.get("class_id"),
            student_id=payload.get("student_id"),
            assignment_type=payload["assignment_type"],
            ref_id=payload["ref_id"],
            title=payload["title"],
            instructions=payload["instructions"],
            subject=payload["subject"],
            sss_level=payload["sss_level"],
            term=payload["term"],
            due_at=payload["due_at"],
            status="assigned",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    def create_intervention(self, payload):
        return SimpleNamespace(
            id=uuid4(),
            teacher_id=payload["teacher_id"],
            class_id=payload.get("class_id"),
            student_id=payload["student_id"],
            intervention_type=payload["intervention_type"],
            severity=payload["severity"],
            subject=payload["subject"],
            sss_level=payload["sss_level"],
            term=payload["term"],
            notes=payload["notes"],
            action_plan=payload.get("action_plan"),
            status="open",
            resolved_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


def test_teacher_service_list_classes_success():
    repo = FakeTeacherRepo()
    service = TeacherService(repo)

    out = service.list_classes(teacher_id=repo.teacher_id)
    assert len(out.classes) == 1
    assert out.classes[0].id == repo.class_id
    assert out.classes[0].enrolled_count == 1


def test_teacher_service_rejects_non_teacher_role():
    repo = FakeTeacherRepo()
    non_teacher_id = uuid4()
    repo.users[non_teacher_id] = SimpleNamespace(id=non_teacher_id, role="student", is_active=True)

    service = TeacherService(repo)
    with pytest.raises(TeacherServiceUnauthorizedError):
        service.list_classes(teacher_id=non_teacher_id)


def test_teacher_service_enroll_students_validates_student_ids():
    repo = FakeTeacherRepo()
    service = TeacherService(repo)
    unknown_student = uuid4()

    with pytest.raises(TeacherServiceValidationError):
        service.enroll_students(
            teacher_id=repo.teacher_id,
            class_id=repo.class_id,
            payload=TeacherClassEnrollIn(student_ids=[unknown_student]),
        )


def test_teacher_service_create_assignment_scope_mismatch_rejected():
    repo = FakeTeacherRepo()
    service = TeacherService(repo)

    payload = TeacherAssignmentCreateIn(
        class_id=repo.class_id,
        student_id=repo.student_id,
        assignment_type="topic",
        ref_id="topic-1",
        title="Math Revision",
        instructions="Revise chapter 1",
        subject="english",
        sss_level="SSS2",
        term=1,
        due_at=None,
    )
    with pytest.raises(TeacherServiceValidationError):
        service.create_assignment(teacher_id=repo.teacher_id, payload=payload)


def test_teacher_service_create_intervention_success():
    repo = FakeTeacherRepo()
    service = TeacherService(repo)

    payload = TeacherInterventionCreateIn(
        class_id=repo.class_id,
        student_id=repo.student_id,
        intervention_type="note",
        severity="medium",
        subject="math",
        sss_level="SSS2",
        term=1,
        notes="Needs extra support on linear equations.",
        action_plan="Schedule one-on-one session.",
    )

    out = service.create_intervention(teacher_id=repo.teacher_id, payload=payload)
    assert out.student_id == repo.student_id
    assert out.intervention_type == "note"
    assert out.status == "open"


def test_teacher_service_create_class_requires_existing_teacher():
    repo = FakeTeacherRepo()
    service = TeacherService(repo)
    payload = TeacherClassCreateIn(
        name="SSS2 Math B",
        description=None,
        subject="math",
        sss_level="SSS2",
        term=1,
    )

    with pytest.raises(TeacherServiceNotFoundError):
        service.create_class(teacher_id=uuid4(), payload=payload)
