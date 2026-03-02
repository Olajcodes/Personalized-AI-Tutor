"""Lesson service (scope enforcement + response assembly)."""

import uuid
from sqlalchemy.orm import Session

from backend.repositories.lesson_repo import (
    get_student_profile,
    student_enrolled_in_subject,
    get_topic_with_subject,
    get_lesson_with_blocks,
)

class LessonNotFound(Exception):
    pass

class ForbiddenLessonAccess(Exception):
    pass


def _map_content_block(block_type: str, content: dict) -> dict:
    payload = {"type": block_type}

    if block_type in {"video", "image"}:
        url = content.get("url") or content.get("value")
        if url is not None:
            payload["url"] = str(url)
            return payload

    if "value" in content:
        payload["value"] = content["value"]
    elif "text" in content:
        payload["value"] = content["text"]
    else:
        payload["value"] = content
    return payload


def fetch_topic_lesson(db: Session, topic_id: uuid.UUID, student_id: uuid.UUID) -> dict:
    # 1) Student context (required for curriculum-bounded access)
    student_profile = get_student_profile(db, student_id)
    if not student_profile:
        raise ForbiddenLessonAccess("Student profile not found. Complete onboarding first.")

    # 2) Topic exists + subject info
    topic_subject = get_topic_with_subject(db, topic_id)
    if not topic_subject:
        raise LessonNotFound("Topic not found.")
    topic, _subject = topic_subject

    # 3) Governance: approved only
    if not topic.is_approved:
        raise ForbiddenLessonAccess("Topic is not approved.")

    # 4) Scope enforcement: level + term
    if topic.sss_level != student_profile.sss_level:
        raise ForbiddenLessonAccess("Topic level out of scope for student.")
    if int(topic.term) != int(student_profile.active_term):
        raise ForbiddenLessonAccess("Topic term out of scope for student.")

    # 5) Enrollment enforcement: student must be enrolled in subject
    if not student_enrolled_in_subject(db, student_profile.id, topic.subject_id):
        raise ForbiddenLessonAccess("Student is not enrolled in this subject.")

    # 6) Lesson exists (1:1 with topic)
    lesson = get_lesson_with_blocks(db, topic.id)
    if not lesson:
        raise LessonNotFound("Lesson not found for this topic.")

    # 7) Assemble response (normalized contract)
    return {
        "topic_id": str(topic.id),
        "title": lesson.title or topic.title,
        "summary": getattr(lesson, "summary", None),
        "estimated_duration_minutes": getattr(lesson, "estimated_duration_minutes", None),
        "content_blocks": [
            _map_content_block(b.block_type, b.content or {})
            for b in lesson.blocks
        ],
    }
