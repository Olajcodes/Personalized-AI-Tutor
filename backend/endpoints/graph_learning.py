from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.graph_learning_schema import LessonGraphContextOut, WhyThisTopicOut
from backend.services.lesson_graph_service import LessonGraphValidationError, lesson_graph_service


router = APIRouter(prefix="/learning/graph", tags=["Learning Graph"])


@router.get("/lesson-context", response_model=LessonGraphContextOut)
def get_lesson_graph_context(
    student_id: UUID,
    subject: Literal["math", "english", "civic"],
    sss_level: Literal["SSS1", "SSS2", "SSS3"],
    term: int = Query(..., ge=1, le=3),
    topic_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )
    try:
        return lesson_graph_service.get_lesson_graph_context(
            db,
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
        )
    except LessonGraphValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/why-this-topic", response_model=WhyThisTopicOut)
def explain_why_this_topic(
    student_id: UUID,
    subject: Literal["math", "english", "civic"],
    sss_level: Literal["SSS1", "SSS2", "SSS3"],
    term: int = Query(..., ge=1, le=3),
    topic_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )
    try:
        return lesson_graph_service.explain_why_this_topic(
            db,
            student_id=student_id,
            subject=subject,
            sss_level=sss_level,
            term=term,
            topic_id=topic_id,
        )
    except LessonGraphValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
