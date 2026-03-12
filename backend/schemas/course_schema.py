from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.learning_path_schema import PathNextOut


class CourseBootstrapTopicOut(BaseModel):
    topic_id: str
    title: str
    description: str | None = None
    lesson_title: str | None = None
    estimated_duration_minutes: int | None = None
    lesson_ready: bool = False
    lesson_unavailable_reason: str | None = None
    sss_level: str
    term: int
    subject_id: str
    status: Literal["mastered", "current", "locked", "ready", "unmapped", "pending"] = "pending"
    mastery_score: float = Field(default=0.0, ge=0.0, le=1.0)
    concept_label: str | None = None
    graph_details: str | None = None
    is_recommended: bool = False


class CourseBootstrapOut(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topics: list[CourseBootstrapTopicOut] = Field(default_factory=list)
    next_step: PathNextOut | None = None
    map_error: str | None = None
    warmed_topic_ids: list[str] = Field(default_factory=list)
    cache_hit_topic_ids: list[str] = Field(default_factory=list)
    failed_topic_ids: list[str] = Field(default_factory=list)
