"""Lesson repository (DB queries only)."""

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.topic import Topic
from backend.models.lesson import Lesson
from backend.models.student import StudentProfile, StudentSubject
from backend.models.subject import Subject

def get_student_profile(db: Session, student_id: uuid.UUID) -> StudentProfile | None:
    stmt = select(StudentProfile).where(StudentProfile.student_id == student_id)
    return db.execute(stmt).scalar_one_or_none()

def student_enrolled_in_subject(db: Session, student_profile_id: uuid.UUID, subject_id: uuid.UUID) -> bool:
    stmt = select(StudentSubject).where(
        StudentSubject.student_profile_id == student_profile_id,
        StudentSubject.subject_id == subject_id
    )
    return db.execute(stmt).first() is not None

def get_topic_with_subject(db: Session, topic_id: uuid.UUID) -> tuple[Topic, Subject] | None:
    stmt = select(Topic, Subject).join(Subject, Subject.id == Topic.subject_id).where(Topic.id == topic_id)
    row = db.execute(stmt).first()
    if not row:
        return None
    return row[0], row[1]

def get_lesson_with_blocks(db: Session, topic_id: uuid.UUID) -> Lesson | None:
    stmt = select(Lesson).where(Lesson.topic_id == topic_id)
    return db.execute(stmt).scalar_one_or_none()