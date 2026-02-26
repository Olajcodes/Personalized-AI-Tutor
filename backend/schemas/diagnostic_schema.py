from typing import List, Dict
from uuid import UUID
from pydantic import BaseModel, Field

class DiagnosticQuestionOut(BaseModel):
    question_id: UUID
    text: str
    options: List[str]

class DiagnosticStartIn(BaseModel):
    student_id: UUID
    subject: str = Field(..., json_schema_extra={"example": "math"})
    sss_level: str = Field(..., json_schema_extra={"example": "SSS1"})

class DiagnosticStartOut(BaseModel):
    diagnostic_id: UUID
    concept_targets: List[str]
    questions: List[DiagnosticQuestionOut]

class DiagnosticAnswerIn(BaseModel):
    question_id: UUID
    selected_option_index: int

class DiagnosticSubmitIn(BaseModel):
    diagnostic_id: UUID
    student_id: UUID
    answers: List[DiagnosticAnswerIn]

class DiagnosticSubmitOut(BaseModel):
    mastery_updates: Dict[str, float]
    recommended_topic_id: UUID
    recommended_topic_title: str
