from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.student_schema import LearningPreferenceResponse, LearningPreferenceUpdateRequest
from backend.services.student_service import StudentService

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/{user_id}/preferences", response_model=LearningPreferenceResponse)
def update_preferences(
    user_id: UUID,
    updates: LearningPreferenceUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's preferences",
        )

    return StudentService(db).update_preferences(user_id, updates)
