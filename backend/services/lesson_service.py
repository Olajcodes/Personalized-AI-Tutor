"""Lesson service (scope enforcement + response assembly)."""

from sqlalchemy.orm import Session
from backend.repositories.lesson_repo import get_topic, get_lesson_by_topic, get_blocks
from backend.repositories.student_repo import get_student_scope

class LessonAccessError(Exception):
    pass

def fetch_topic_lesson(db: Session, topic_id: str, student_id: str) -> dict:
    student = get_student_scope(db, student_id)

    topic = get_topic(db, topic_id)
    if not topic:
        raise FileNotFoundError("Topic not found")

    if not topic.is_approved:
        raise LessonAccessError("Topic is not approved")

    # Curriculum scope checks (SSS level + term)
    if topic.sss_level != student["sss_level"]:
        raise LessonAccessError("Topic level out of scope")

    if int(topic.term) != int(student["term"]):
        raise LessonAccessError("Topic term out of scope")

    # Subject enrollment check
    if topic.subject not in student["subjects"]:
        raise LessonAccessError("Subject not enrolled for student")

    lesson = get_lesson_by_topic(db, topic_id)
    if not lesson:
        raise FileNotFoundError("Lesson not found for topic")

    blocks = get_blocks(db, lesson.id)

    return {
        "topic_id": topic.id,
        "title": topic.title,
        "subject": topic.subject,
        "sss_level": topic.sss_level,
        "term": topic.term,
        "lesson": {
            "lesson_id": lesson.id,
            "summary": lesson.summary,
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
            "blocks": [{"block_type": b.block_type, "content": b.content} for b in blocks],
        },
    }
