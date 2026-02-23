"""Lesson content schemas.

Logic:
- Response uses 'blocks' so frontend can render different content types consistently.
"""

from pydantic import BaseModel
from typing import List, Literal, Optional

BlockType = Literal["text", "video", "image", "example", "exercise"]

class LessonBlockOut(BaseModel):
    block_type: BlockType
    content: str

class LessonOut(BaseModel):
    lesson_id: str
    summary: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    blocks: List[LessonBlockOut]

class TopicLessonResponse(BaseModel):
    topic_id: str
    title: str
    subject: str
    sss_level: str
    term: int
    lesson: LessonOut
