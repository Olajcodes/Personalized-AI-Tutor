from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime

# --- Enums (mirror API spec) ---
QuizPurpose = Literal["practice", "diagnostic", "exam_prep"]
Difficulty = Literal["easy", "medium", "hard"]

# --- Request Schemas ---
class QuizGenerateRequest(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID
    purpose: QuizPurpose
    difficulty: Difficulty
    num_questions: int = Field(10, ge=1, le=50)

class QuizSubmitRequest(BaseModel):
    student_id: UUID
    answers: List[dict]  # list of {question_id: UUID, answer: str} – exact format TBD
    time_taken_seconds: int = Field(..., ge=0)

# --- Response Schemas ---
class QuestionSchema(BaseModel):
    id: UUID
    text: str
    options: Optional[List[str]]  # for multiple choice
    correct_answer: Optional[str]  # maybe omitted for security
    concept_id: UUID
    difficulty: Difficulty

class QuizGenerateResponse(BaseModel):
    quiz_id: UUID
    questions: List[QuestionSchema]

class QuizSubmitResponse(BaseModel):
    attempt_id: UUID
    score: float  # 0-100
    xp_awarded: int

class ConceptBreakdownItem(BaseModel):
    concept_id: UUID
    correct: bool
    mastery_delta: float

class QuizResultsResponse(BaseModel):
    score: float
    concept_breakdown: List[ConceptBreakdownItem]
    insights: List[str]
    recommended_revision_topic_id: Optional[UUID]

# --- Internal Graph Update Payload (matches spec) ---
class GraphMasteryUpdatePayload(BaseModel):
    student_id: UUID
    quiz_id: UUID
    attempt_id: UUID
    subject: str
    sss_level: str
    term: int
    timestamp: datetime
    source: Literal["practice", "diagnostic", "exam_prep"]
    concept_breakdown: List[ConceptBreakdownItem]