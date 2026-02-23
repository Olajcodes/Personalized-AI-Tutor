"""Pydantic models for FastAPI ↔ ai-core contract."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional


class TutorRequest(BaseModel):
    user_id: str
    role: Literal["student", "teacher", "admin"] = "student"
    jss_level: Literal["JSS1", "JSS2", "JSS3"]
    term: Literal[1, 2, 3]
    subject_id: str
    topic_id: Optional[str] = None
    mode: Literal["explain", "practice", "revise", "exam_prep"] = "explain"
    message: str
    session_id: Optional[str] = None


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    snippet: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TutorResponse(BaseModel):
    assistant_message: str
    citations: List[Citation] = Field(default_factory=list)
    remediation_prereqs: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    cost: Dict[str, Any] = Field(default_factory=dict)
