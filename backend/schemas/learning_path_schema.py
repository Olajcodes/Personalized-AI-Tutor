from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class PathNextIn(BaseModel):
    student_id: UUID
    subject: str

class PathNextOut(BaseModel):
    recommended_topic_id: UUID
    title: str
    description: Optional[str]
    prerequisite_gaps: List[str]
    estimated_duration_minutes: int