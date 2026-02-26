from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

class InternalGraphContextOut(BaseModel):
    student_id: UUID
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    overall_mastery: float

class InternalGraphUpdateIn(BaseModel):
    student_id: UUID
    concept_id: str
    mastery_increment: float

class InternalGraphUpdateOut(BaseModel):
    success: bool
    new_mastery: float