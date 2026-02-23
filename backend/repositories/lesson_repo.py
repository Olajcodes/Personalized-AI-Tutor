"""Lesson repository (DB queries only)."""

from sqlalchemy.orm import Session
from backend.models.topic import Topic
from backend.models.lesson import Lesson, LessonBlock

def get_topic(db: Session, topic_id: str) -> Topic | None:
    return db.query(Topic).filter(Topic.id == topic_id).first()

def get_lesson_by_topic(db: Session, topic_id: str) -> Lesson | None:
    return db.query(Lesson).filter(Lesson.topic_id == topic_id).first()

def get_blocks(db: Session, lesson_id: str) -> list[LessonBlock]:
    return (
        db.query(LessonBlock)
        .filter(LessonBlock.lesson_id == lesson_id)
        .order_by(LessonBlock.order_index.asc())
        .all()
    )
