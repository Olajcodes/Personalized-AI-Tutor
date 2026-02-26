from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

QuizPurpose = Literal["practice", "diagnostic", "exam_prep"]
Difficulty = Literal["easy", "medium", "hard"]
SupportedSubject = Literal["math", "english", "civic"]
SupportedLevel = Literal["SSS1", "SSS2", "SSS3"]


class QuizGenerateRequest(BaseModel):
    student_id: UUID
    subject: SupportedSubject
    sss_level: SupportedLevel
    term: Literal[1, 2, 3]
    topic_id: UUID
    purpose: QuizPurpose
    difficulty: Difficulty
    num_questions: int = Field(default=10, ge=1, le=50)


class QuizAnswerIn(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=255)


class QuizSubmitRequest(BaseModel):
    student_id: UUID
    answers: list[QuizAnswerIn] = Field(default_factory=list)
    time_taken_seconds: int = Field(ge=0)


class QuestionSchema(BaseModel):
    id: UUID
    text: str
    options: list[str] | None = None
    correct_answer: str | None = None
    concept_id: str
    difficulty: Difficulty


class QuizGenerateResponse(BaseModel):
    quiz_id: UUID
    questions: list[QuestionSchema]


class QuizSubmitResponse(BaseModel):
    attempt_id: UUID
    score: float
    xp_awarded: int


class ConceptBreakdownItem(BaseModel):
    concept_id: str
    is_correct: bool
    weight_change: float


class QuizResultsResponse(BaseModel):
    score: float
    concept_breakdown: list[ConceptBreakdownItem]
    insights: list[str]
    recommended_revision_topic_id: UUID | None


class GraphMasteryUpdatePayload(BaseModel):
    student_id: UUID
    quiz_id: UUID
    attempt_id: UUID
    subject: SupportedSubject
    sss_level: SupportedLevel
    term: int = Field(ge=1, le=3)
    timestamp: datetime
    source: QuizPurpose
    concept_breakdown: list[ConceptBreakdownItem]
