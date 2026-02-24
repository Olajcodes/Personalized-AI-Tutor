from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from backend.core.database import get_db
from backend.services.student_service import StudentService
from backend.schemas.student_schema import (
    StudentProfileSetupRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    LearningPreferenceUpdateRequest,
    LearningPreferenceResponse,
)
from backend.core.auth import get_current_user  # Assumes auth team provides this

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/profile/setup", response_model=StudentProfileResponse)
async def setup_profile(
    request: StudentProfileSetupRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)   # Ensures user is authenticated
):
    """Create initial student profile with context."""
    service = StudentService(db)
    return service.setup_profile(request)

@router.get("/profile", response_model=StudentProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current student's profile."""
    service = StudentService(db)
    # current_user should have an 'id' field that matches student_id in our model
    return service.get_profile(current_user.id)

@router.put("/profile", response_model=StudentProfileResponse)
async def update_profile(
    updates: StudentProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update standard profile fields."""
    service = StudentService(db)
    return service.update_profile(current_user.id, updates)

@router.put("/users/{user_id}/preferences", response_model=LearningPreferenceResponse)
async def update_preferences(
    user_id: UUID,
    updates: LearningPreferenceUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update learning preferences for a user."""
    # Ensure user can only update their own preferences
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's preferences"
        )
    service = StudentService(db)
    return service.update_preferences(user_id, updates)