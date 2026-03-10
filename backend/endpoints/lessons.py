"""Lesson content delivery endpoints.

Exposes topic lesson retrieval with student-scope authorization checks.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.lesson_schema import TopicLessonResponse
from backend.services.lesson_service import (
    fetch_topic_lesson,
    LessonNotFound,
    ForbiddenLessonAccess,
    LessonGenerationError,
)

router = APIRouter(prefix="/learning", tags=["Lessons"])

@router.get("/topics/{topic_id}/lesson", response_model=TopicLessonResponse)
def get_topic_lesson(
    topic_id: uuid.UUID,
    student_id: uuid.UUID = Query(..., description="Student UUID for curriculum scope enforcement"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return lesson content blocks for a specific topic.

    Access is restricted to topics that are valid for the requesting student's
    configured learning scope.
    """
    if student_id != current_user.id:
        raise HTTPException(status_code=403, detail="student_id must match authenticated user id")
    try:
        return fetch_topic_lesson(db=db, topic_id=topic_id, student_id=student_id)
    except LessonNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenLessonAccess as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LessonGenerationError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {e}")
