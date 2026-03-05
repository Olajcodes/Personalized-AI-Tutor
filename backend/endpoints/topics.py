"""Topic listing endpoints constrained by student profile scope."""

import uuid
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.core.database import get_db
from backend.models.topic import Topic
from backend.models.subject import Subject
from backend.models.student import StudentProfile, StudentSubject
from backend.models.personalized_lesson import PersonalizedLesson

router = APIRouter(prefix="/learning", tags=["Topics"])


_NOISY_DESCRIPTION_MARKERS = (
    "SECOND TERM E-LEARNING NOTE SUBJECT",
    "SCHEME OF WORK WEEK TOPIC",
    "WEEKEND ASSIGNMENT SECTION",
)


def _clean_topic_description(raw: str | None, topic_title: str) -> str:
    text = re.sub(r"\s+", " ", str(raw or "")).strip()
    if not text:
        return f"{topic_title} is available for personalized lesson generation."
    if any(marker in text.upper() for marker in _NOISY_DESCRIPTION_MARKERS):
        return f"{topic_title} is available for personalized lesson generation."
    if len(text) > 220:
        return f"{text[:217].rstrip()}..."
    return text

@router.get("/topics")
def list_topics(
    student_id: uuid.UUID = Query(...),
    subject: str | None = Query(None, description="math|english|civic"),
    term: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Return approved topics available to the student in current scope.

    Topic visibility is restricted by student profile level/term/subjects.
    Optional `subject` and `term` query params narrow the result.
    """
    # Fetch student scope
    sp = db.execute(select(StudentProfile).where(StudentProfile.student_id == student_id)).scalar_one_or_none()
    if not sp:
        raise HTTPException(status_code=403, detail="Student profile not found.")

    # Subjects the student is enrolled in
    enrolled_subject_ids = [
        row[0] for row in db.execute(
            select(StudentSubject.subject_id).where(StudentSubject.student_profile_id == sp.id)
        ).all()
    ]

    q = (
        select(Topic, PersonalizedLesson)
        .outerjoin(
            PersonalizedLesson,
            (PersonalizedLesson.topic_id == Topic.id)
            & (PersonalizedLesson.student_id == student_id),
        )
        .where(
        Topic.is_approved.is_(True),
        Topic.sss_level == sp.sss_level,
        Topic.term == (term if term is not None else sp.active_term),
        Topic.subject_id.in_(enrolled_subject_ids),
        )
    )

    if subject is not None:
        q = q.join(Subject, Subject.id == Topic.subject_id).where(Subject.slug == subject.lower())

    q = q.order_by(Topic.created_at.asc(), Topic.title.asc())
    rows = db.execute(q).all()
    payload = []
    for topic, personalized_lesson in rows:
        description = (
            personalized_lesson.summary
            if personalized_lesson and personalized_lesson.summary
            else _clean_topic_description(topic.description, topic.title)
        )
        payload.append(
            {
                "topic_id": str(topic.id),
                "title": topic.title,
                "description": description,
                "lesson_title": personalized_lesson.title if personalized_lesson else None,
                "estimated_duration_minutes": (
                    personalized_lesson.estimated_duration_minutes if personalized_lesson else None
                ),
                "sss_level": topic.sss_level,
                "term": topic.term,
                "subject_id": str(topic.subject_id),
            }
        )
    return payload
