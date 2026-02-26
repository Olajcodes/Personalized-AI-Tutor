from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PathNextIn(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: int = Field(ge=1, le=3)


class PathNextOut(BaseModel):
    recommended_topic_id: str | None
    reason: str
    prereq_gaps: list[str]


class LearningMapNodeOut(BaseModel):
    topic_id: str
    concept_id: str
    status: Literal["mastered", "current", "locked"]
    mastery_score: float


class LearningMapVisualOut(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: int = Field(ge=1, le=3)
    view: Literal["topic", "concept"]
    nodes: list[LearningMapNodeOut]
