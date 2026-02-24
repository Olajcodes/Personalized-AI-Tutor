from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException, status

from ..repositories.student_repo import StudentRepository
from ..schemas.student_schema import (
    StudentProfileSetupRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    LearningPreferenceUpdateRequest,
    LearningPreferenceResponse
)

class StudentService:
    def __init__(self, db: Session):
        self.repo = StudentRepository(db)
    
    def setup_profile(self, request: StudentProfileSetupRequest) -> StudentProfileResponse:
        """Setup initial student profile"""
        # Check if profile already exists
        existing = self.repo.get_profile(request.student_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists for this student"
            )
        
        student = self.repo.create_profile(request)
        return self._to_profile_response(student)
    
    def get_profile(self, student_id: UUID) -> StudentProfileResponse:
        """Get student profile"""
        student = self.repo.get_profile(student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        return self._to_profile_response(student)
    
    def get_profile_by_user_id(self, user_id: UUID) -> StudentProfileResponse:
        """Get student profile by user ID"""
        student = self.repo.get_profile_by_user_id(user_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found for this user"
            )
        return self._to_profile_response(student)
    
    def update_profile(self, student_id: UUID, updates: StudentProfileUpdateRequest) -> StudentProfileResponse:
        """Update student profile"""
        student = self.repo.update_profile(student_id, updates)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        return self._to_profile_response(student)
    
    def update_preferences(self, user_id: UUID, updates: LearningPreferenceUpdateRequest) -> LearningPreferenceResponse:
        """Update learning preferences"""
        # First get student by user_id
        student = self.repo.get_profile_by_user_id(user_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found for this user"
            )
        
        preferences = self.repo.update_preferences(student.id, updates)
        return self._to_preference_response(preferences)
    
    def _to_profile_response(self, student) -> StudentProfileResponse:
        """Convert Student model to response schema"""
        active_subjects = self.repo.get_active_subjects(student.id)
        
        return StudentProfileResponse(
            id=student.id,
            user_id=student.user_id,
            sss_level=student.sss_level,
            current_term=student.current_term,
            subjects=active_subjects,
            preferences=self._to_preference_response(student.preferences) if student.preferences else None,
            created_at=student.created_at,
            updated_at=student.updated_at
        )
    
    def _to_preference_response(self, preferences) -> LearningPreferenceResponse:
        """Convert LearningPreference model to response schema"""
        return LearningPreferenceResponse(
            student_id=preferences.student_id,
            explanation_depth=preferences.explanation_depth,
            examples_first=preferences.examples_first,
            pace=preferences.pace,
            updated_at=preferences.updated_at
        )