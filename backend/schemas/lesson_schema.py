"""Lesson content schemas.

Logic:
- Response matches the normalized contract for lesson delivery.
- Includes graph-backed lesson context used by the student cockpit.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

BlockType = Literal["text", "video", "image", "example", "exercise"]


class ContentBlockOut(BaseModel):
    type: BlockType
    value: Any | None = None
    url: str | None = None


class LessonConceptOut(BaseModel):
    concept_id: str
    label: str
    mastery_score: float | None = Field(default=None, ge=0.0, le=1.0)
    mastery_state: Literal["demonstrated", "needs_review", "unassessed"] | None = None


class LessonNextUnlockOut(BaseModel):
    concept_id: str | None = None
    concept_label: str | None = None
    topic_id: str | None = None
    topic_title: str | None = None
    reason: str | None = None


class TopicLessonResponse(BaseModel):
    topic_id: str
    title: str
    summary: str | None = None
    estimated_duration_minutes: int | None = None
    content_blocks: list[ContentBlockOut]
    covered_concepts: list[LessonConceptOut] = Field(default_factory=list)
    prerequisites: list[LessonConceptOut] = Field(default_factory=list)
    weakest_concepts: list[LessonConceptOut] = Field(default_factory=list)
    next_unlock: LessonNextUnlockOut | None = None
    why_this_matters: str | None = None
    assessment_ready: bool = False
