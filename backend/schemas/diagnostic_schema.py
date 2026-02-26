from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DiagnosticQuestionOut(BaseModel):
    question_id: str
    concept_id: str
    prompt: str
    options: list[str]


class DiagnosticStartIn(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"] = Field(..., json_schema_extra={"example": "math"})
    sss_level: Literal["SSS1", "SSS2", "SSS3"] = Field(..., json_schema_extra={"example": "SSS1"})
    term: int = Field(..., ge=1, le=3)


class DiagnosticStartOut(BaseModel):
    diagnostic_id: UUID
    concept_targets: list[str]
    questions: list[DiagnosticQuestionOut]


class DiagnosticAnswerIn(BaseModel):
    question_id: str
    answer: str = Field(min_length=1, max_length=4)


class DiagnosticSubmitIn(BaseModel):
    diagnostic_id: UUID
    student_id: UUID
    answers: list[DiagnosticAnswerIn]


class BaselineMasteryUpdateOut(BaseModel):
    concept_id: str
    previous_score: float
    new_score: float
    delta: float


class DiagnosticSubmitOut(BaseModel):
    baseline_mastery_updates: list[BaselineMasteryUpdateOut]
    recommended_start_topic_id: str | None
