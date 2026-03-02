"""Lesson content schemas.

Logic:
- Response matches the normalized contract for lesson delivery.
"""

from typing import Any, Literal

from pydantic import BaseModel

BlockType = Literal["text", "video", "image", "example", "exercise"]


class ContentBlockOut(BaseModel):
    type: BlockType
    value: Any | None = None
    url: str | None = None


class TopicLessonResponse(BaseModel):
    topic_id: str
    title: str
    summary: str | None = None
    estimated_duration_minutes: int | None = None
    content_blocks: list[ContentBlockOut]
