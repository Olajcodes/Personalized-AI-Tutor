"""Lesson + LessonBlock ORM models.

Logic:
- Lesson is attached to a Topic.
- LessonBlocks store structured content in a stable display order.
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from backend.core.database import Base

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String, primary_key=True)  # UUID as string (MVP)
    topic_id = Column(String, ForeignKey("topics.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)

class LessonBlock(Base):
    __tablename__ = "lesson_blocks"

    id = Column(String, primary_key=True)  # UUID as string (MVP)
    lesson_id = Column(String, ForeignKey("lessons.id"), nullable=False, index=True)
    block_type = Column(String, nullable=False)  # text|video|image|example|exercise
    content = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, index=True)
