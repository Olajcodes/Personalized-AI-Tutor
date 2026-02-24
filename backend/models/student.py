from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base

# Association table for student-subjects many-to-many relationship
student_subjects = Table(
    'student_subjects',
    Base.metadata,
    Column('student_id', UUID(as_uuid=True), ForeignKey('students.id')),
    Column('subject', String(50)),
    Column('is_active', Boolean, default=True)
)

class Student(Base):
    __tablename__ = "students"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True)
    sss_level = Column(String(10), nullable=False)  # SSS1, SSS2, SSS3
    current_term = Column(Integer, nullable=False)  # 1, 2, 3
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    preferences = relationship("LearningPreference", back_populates="student", uselist=False)
    subjects = relationship("StudentSubject", back_populates="student")
    
class LearningPreference(Base):
    __tablename__ = "learning_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), unique=True)
    explanation_depth = Column(String(20), default="standard")  # simple, standard, detailed
    examples_first = Column(Boolean, default=False)
    pace = Column(String(20), default="normal")  # slow, normal, fast
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="preferences")

class StudentSubject(Base):
    __tablename__ = "student_subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'))
    subject = Column(String(50), nullable=False)  # math, english, civic
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="subjects")