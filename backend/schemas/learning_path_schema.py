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
    recommended_topic_title: str | None = None
    recommended_concept_id: str | None = None
    recommended_concept_label: str | None = None
    reason: str
    prereq_gaps: list[str]


class LearningMapNodeOut(BaseModel):
    topic_id: str
    concept_id: str
    title: str
    details: str | None = None
    status: Literal["mastered", "current", "locked", "ready"]
    mastery_score: float
    concept_label: str | None = None
    kind: Literal["topic", "concept"] = "topic"


class LearningMapVisualOut(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: int = Field(ge=1, le=3)
    view: Literal["topic", "concept"]
    nodes: list[LearningMapNodeOut]
