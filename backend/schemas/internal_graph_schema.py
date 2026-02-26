from datetime import datetime
from typing import Any, Dict, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class InternalGraphContextOut(BaseModel):
    student_id: UUID
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    overall_mastery: float


class ConceptUpdateIn(BaseModel):
    concept_id: str
    is_correct: bool
    weight_change: float


class InternalGraphUpdateIn(BaseModel):
    student_id: UUID
    quiz_id: UUID
    attempt_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: int = Field(ge=1, le=3)
    timestamp: datetime
    source: Literal["practice", "diagnostic", "exam_prep"]
    concept_breakdown: List[ConceptUpdateIn]


class InternalGraphUpdateOut(BaseModel):
    success: bool
    new_mastery: float
    updated_concepts: int = 0
