"""Lesson content schemas.

Logic:
- Response uses 'blocks' so frontend can render different content types consistently.
"""

from pydantic import BaseModel
from typing import Literal, List, Optional, Dict, Any

BlockType = Literal["text", "video", "image", "example", "exercise"]

class LessonBlockOut(BaseModel):
    block_type: BlockType
    content: Dict[str, Any]
    order_index: int

class LessonOut(BaseModel):
    lesson_id: str
    title: str
    summary: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    blocks: List[LessonBlockOut]

class TopicLessonResponse(BaseModel):
    topic_id: str
    topic_title: str
    subject: str
    sss_level: str
    term: int
    lesson: LessonOut