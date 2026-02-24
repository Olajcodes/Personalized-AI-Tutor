import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.lesson_schema import TopicLessonResponse
from backend.services.lesson_service import fetch_topic_lesson, LessonNotFound, ForbiddenLessonAccess

router = APIRouter(prefix="/learning", tags=["Lessons"])

@router.get("/topics/{topic_id}/lesson", response_model=TopicLessonResponse)
def get_topic_lesson(
    topic_id: uuid.UUID,
    student_id: uuid.UUID = Query(..., description="Student UUID for curriculum scope enforcement"),
    db: Session = Depends(get_db),
):
    try:
        return fetch_topic_lesson(db=db, topic_id=topic_id, student_id=student_id)
    except LessonNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenLessonAccess as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected server error")