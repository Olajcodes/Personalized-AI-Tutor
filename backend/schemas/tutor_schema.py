from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TutorCitationOut(BaseModel):
    source_id: str
    chunk_id: str
    snippet: str


class TutorRecommendationOut(BaseModel):
    type: str
    topic_id: str | None = None
    reason: str


class TutorChatIn(BaseModel):
    student_id: UUID
    session_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID | None = None
    message: str = Field(min_length=1, max_length=4000)


class TutorChatOut(BaseModel):
    assistant_message: str
    citations: list[TutorCitationOut] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    recommendations: list[TutorRecommendationOut] = Field(default_factory=list)


class TutorAssessmentStartIn(BaseModel):
    student_id: UUID
    session_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class TutorAssessmentStartOut(BaseModel):
    assessment_id: UUID
    question: str
    concept_id: str = Field(min_length=1, max_length=255)
    concept_label: str = Field(min_length=1, max_length=255)
    ideal_answer: str = Field(min_length=1)
    hint: str | None = None
    citations: list[TutorCitationOut] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class TutorAssessmentSubmitIn(BaseModel):
    student_id: UUID
    session_id: UUID
    assessment_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID
    answer: str = Field(min_length=1, max_length=2000)


class TutorAssessmentSubmitOut(BaseModel):
    assessment_id: UUID
    is_correct: bool
    score: float = Field(ge=0.0, le=1.0)
    feedback: str
    ideal_answer: str
    concept_id: str = Field(min_length=1, max_length=255)
    concept_label: str = Field(min_length=1, max_length=255)
    mastery_updated: bool
    new_mastery: float | None = Field(default=None, ge=0.0, le=1.0)
    actions: list[str] = Field(default_factory=list)


class TutorHintIn(BaseModel):
    student_id: UUID
    session_id: UUID | None = None
    quiz_id: UUID
    question_id: str = Field(min_length=1, max_length=255)
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID | None = None
    message: str | None = Field(default=None, max_length=1000)


class TutorHintOut(BaseModel):
    hint: str
    strategy: str = "guided_hint"


class TutorExplainMistakeIn(BaseModel):
    student_id: UUID
    session_id: UUID | None = None
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID | None = None
    question: str = Field(min_length=1, max_length=2000)
    student_answer: str = Field(min_length=1, max_length=255)
    correct_answer: str = Field(min_length=1, max_length=255)


class TutorExplainMistakeOut(BaseModel):
    explanation: str
    improvement_tip: str
