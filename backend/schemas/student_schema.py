from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import enum

# Enums for validation
class SSSLevel(str, enum.Enum):
    SSS1 = "SSS1"
    SSS2 = "SSS2"
    SSS3 = "SSS3"

class Subject(str, enum.Enum):
    MATH = "math"
    ENGLISH = "english"
    CIVIC = "civic"

class Term(int, enum.Enum):
    TERM_1 = 1
    TERM_2 = 2
    TERM_3 = 3

class ExplanationDepth(str, enum.Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    DETAILED = "detailed"

class Pace(str, enum.Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"

# Requests
class StudentProfileSetupRequest(BaseModel):
    student_id: UUID
    sss_level: SSSLevel
    subjects: List[Subject]
    term: Term

class StudentProfileUpdateRequest(BaseModel):
    sss_level: Optional[SSSLevel] = None
    current_term: Optional[Term] = None          # API uses "current_term" for updates too
    subjects: Optional[List[Subject]] = None

class LearningPreferenceUpdateRequest(BaseModel):
    explanation_depth: Optional[ExplanationDepth] = None
    examples_first: Optional[bool] = None
    pace: Optional[Pace] = None

# Responses
class LearningPreferenceResponse(BaseModel):
    student_id: UUID
    explanation_depth: str
    examples_first: bool
    pace: str
    updated_at: datetime

class StudentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    sss_level: str
    current_term: int                # API spec uses "current_term"
    subjects: List[str]
    preferences: Optional[LearningPreferenceResponse] = None
    created_at: datetime
    updated_at: datetime


class StudentProfileStatusResponse(BaseModel):
    """Lightweight onboarding status for authenticated student users."""

    has_profile: bool
    user_id: UUID
