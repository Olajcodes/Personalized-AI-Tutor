import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.core.database import get_db
from backend.models.topic import Topic
from backend.models.subject import Subject
from backend.models.student import StudentProfile, StudentSubject

router = APIRouter(prefix="/learning", tags=["Topics"])

@router.get("/topics")
def list_topics(
    student_id: uuid.UUID = Query(...),
    subject: str | None = Query(None, description="math|english|civic"),
    term: int | None = Query(None),
    db: Session = Depends(get_db),
):
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

    q = select(Topic).where(
        Topic.is_approved.is_(True),
        Topic.sss_level == sp.sss_level,
        Topic.term == (term if term is not None else sp.active_term),
        Topic.subject_id.in_(enrolled_subject_ids),
    )

    if subject is not None:
        q = q.join(Subject, Subject.id == Topic.subject_id).where(Subject.slug == subject.lower())

    topics = db.execute(q).scalars().all()
    return [{
        "topic_id": str(t.id),
        "title": t.title,
        "sss_level": t.sss_level,
        "term": t.term,
        "subject_id": str(t.subject_id),
    } for t in topics]
