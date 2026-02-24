from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID
from typing import List, Optional

from ..models.student import Student, LearningPreference, StudentSubject
from ..schemas.student_schema import (
    StudentProfileSetupRequest,
    StudentProfileUpdateRequest,
    LearningPreferenceUpdateRequest
)

class StudentRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_profile(self, request: StudentProfileSetupRequest) -> Student:
        """Create a new student profile"""
        student = Student(
            id=request.student_id,
            sss_level=request.sss_level,
            current_term=request.term
        )
        self.db.add(student)
        self.db.flush()
        
        # Add subjects
        for subject in request.subjects:
            student_subject = StudentSubject(
                student_id=student.id,
                subject=subject
            )
            self.db.add(student_subject)
        
        # Create default preferences
        preferences = LearningPreference(student_id=student.id)
        self.db.add(preferences)
        
        self.db.commit()
        self.db.refresh(student)
        return student
    
    def get_profile(self, student_id: UUID) -> Optional[Student]:
        """Get student profile by ID"""
        return self.db.query(Student).filter(Student.id == student_id).first()
    
    def get_profile_by_user_id(self, user_id: UUID) -> Optional[Student]:
        """Get student profile by user ID"""
        return self.db.query(Student).filter(Student.user_id == user_id).first()
    
    def update_profile(self, student_id: UUID, updates: StudentProfileUpdateRequest) -> Optional[Student]:
        """Update student profile"""
        student = self.get_profile(student_id)
        if not student:
            return None
        
        # Update fields if provided
        if updates.sss_level:
            student.sss_level = updates.sss_level
        if updates.current_term:
            student.current_term = updates.current_term
        
        # Update subjects if provided
        if updates.subjects is not None:
            # Deactivate all current subjects
            self.db.query(StudentSubject).filter(
                StudentSubject.student_id == student_id
            ).update({"is_active": False})
            
            # Add new subjects
            for subject in updates.subjects:
                # Check if subject already exists
                existing = self.db.query(StudentSubject).filter(
                    and_(
                        StudentSubject.student_id == student_id,
                        StudentSubject.subject == subject
                    )
                ).first()
                
                if existing:
                    existing.is_active = True
                else:
                    new_subject = StudentSubject(
                        student_id=student_id,
                        subject=subject
                    )
                    self.db.add(new_subject)
        
        student.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(student)
        return student
    
    def update_preferences(self, student_id: UUID, updates: LearningPreferenceUpdateRequest) -> Optional[LearningPreference]:
        """Update learning preferences"""
        preferences = self.db.query(LearningPreference).filter(
            LearningPreference.student_id == student_id
        ).first()
        
        if not preferences:
            # Create if doesn't exist
            preferences = LearningPreference(student_id=student_id)
            self.db.add(preferences)
        
        # Update fields if provided
        if updates.explanation_depth:
            preferences.explanation_depth = updates.explanation_depth
        if updates.examples_first is not None:
            preferences.examples_first = updates.examples_first
        if updates.pace:
            preferences.pace = updates.pace
        
        preferences.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
    
    def get_active_subjects(self, student_id: UUID) -> List[str]:
        """Get active subjects for a student"""
        subjects = self.db.query(StudentSubject).filter(
            and_(
                StudentSubject.student_id == student_id,
                StudentSubject.is_active == True
            )
        ).all()
        return [s.subject for s in subjects]