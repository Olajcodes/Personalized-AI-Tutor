"""Shared schemas between AI Core and backend for quiz generation."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

QuizPurpose = Literal["practice", "diagnostic", "exam_prep"]
Difficulty = Literal["easy", "medium", "hard"]
SupportedSubject = Literal["math", "english", "civic"]
SupportedLevel = Literal["SSS1", "SSS2", "SSS3"]


class QuizGenerateRequest(BaseModel):
    subject: SupportedSubject
    sss_level: SupportedLevel
    term: int = Field(ge=1, le=3)
    topic_id: UUID
    purpose: QuizPurpose
    difficulty: Difficulty
    num_questions: int = Field(ge=1, le=50)


class QuestionSchema(BaseModel):
    id: UUID
    text: str
    options: list[str] | None = None
    correct_answer: str | None = None
    concept_id: str
    difficulty: Difficulty


class QuizGenerateResponse(BaseModel):
    questions: list[QuestionSchema]
