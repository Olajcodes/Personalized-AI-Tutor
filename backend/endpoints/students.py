from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..core.database import get_db
from ..services.student_service import StudentService
from ..schemas.student_schema import (
    StudentProfileSetupRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    LearningPreferenceUpdateRequest,
    LearningPreferenceResponse
)
from ..core.auth import get_current_user

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/profile/setup", response_model=StudentProfileResponse)
async def setup_profile(
    request: StudentProfileSetupRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Ensure user is authenticated
):
    """
    Creates baseline learning context required for scoping.
    - student_id: UUID of the student
    - sss_level: SSS1, SSS2, or SSS3
    - subjects: Array of ["math", "english", "civic"]
    - term: 1, 2, or 3
    """
    service = StudentService(db)
    return service.setup_profile(request)

@router.get("/profile", response_model=StudentProfileResponse)
async def get_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Returns student profile + active context.
    Uses the authenticated user's ID to fetch their student profile.
    """
    service = StudentService(db)
    # Assuming current_user has an id field
    return service.get_profile_by_user_id(current_user.id)

@router.put("/profile", response_model=StudentProfileResponse)
async def update_profile(
    updates: StudentProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Updates standard profile fields (non-AI).
    """
    service = StudentService(db)
    student = service.get_profile_by_user_id(current_user.id)
    return service.update_profile(student.id, updates)

@router.put("/users/{user_id}/preferences", response_model=LearningPreferenceResponse)
async def update_preferences(
    user_id: UUID,
    updates: LearningPreferenceUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Updates learning preferences.
    - explanation_depth: simple|standard|detailed
    - examples_first: true|false
    - pace: slow|normal|fast
    """
    # Optional: Check if current_user has permission to update this user's preferences
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's preferences"
        )
    
    service = StudentService(db)
    return service.update_preferences(user_id, updates)