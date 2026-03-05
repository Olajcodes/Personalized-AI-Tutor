"""Lesson repository (DB queries only)."""

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.topic import Topic
from backend.models.lesson import Lesson
from backend.models.personalized_lesson import PersonalizedLesson
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


def ensure_personalized_lessons_table(db: Session) -> None:
    bind = db.get_bind()
    PersonalizedLesson.__table__.create(bind=bind, checkfirst=True)


def get_personalized_lesson(
    db: Session,
    *,
    student_id: uuid.UUID,
    topic_id: uuid.UUID,
) -> PersonalizedLesson | None:
    stmt = select(PersonalizedLesson).where(
        PersonalizedLesson.student_id == student_id,
        PersonalizedLesson.topic_id == topic_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def upsert_personalized_lesson(
    db: Session,
    *,
    student_id: uuid.UUID,
    topic_id: uuid.UUID,
    curriculum_version_id: uuid.UUID | None,
    title: str,
    summary: str | None,
    estimated_duration_minutes: int | None,
    content_blocks: list,
    source_chunk_ids: list[str],
    generation_metadata: dict,
) -> PersonalizedLesson:
    row = get_personalized_lesson(db, student_id=student_id, topic_id=topic_id)
    if row is None:
        row = PersonalizedLesson(
            student_id=student_id,
            topic_id=topic_id,
            curriculum_version_id=curriculum_version_id,
            title=title,
            summary=summary,
            estimated_duration_minutes=estimated_duration_minutes,
            content_blocks=list(content_blocks or []),
            source_chunk_ids=list(source_chunk_ids or []),
            generation_metadata=dict(generation_metadata or {}),
        )
        db.add(row)
        db.flush()
        return row

    row.curriculum_version_id = curriculum_version_id
    row.title = title
    row.summary = summary
    row.estimated_duration_minutes = estimated_duration_minutes
    row.content_blocks = list(content_blocks or [])
    row.source_chunk_ids = list(source_chunk_ids or [])
    row.generation_metadata = dict(generation_metadata or {})
    db.flush()
    return row
