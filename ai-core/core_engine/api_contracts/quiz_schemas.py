"""
Shared schemas between AI Core and backend for quiz generation.
"""
from pydantic import BaseModel
from typing import List, Optional, Literal
from uuid import UUID

QuizPurpose = Literal["practice", "diagnostic", "exam_prep"]
Difficulty = Literal["easy", "medium", "hard"]

class QuizGenerateRequest(BaseModel):
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID
    purpose: QuizPurpose
    difficulty: Difficulty
    num_questions: int

class QuestionSchema(BaseModel):
    id: UUID
    text: str
    options: Optional[List[str]]
    correct_answer: str
    concept_id: UUID
    difficulty: Difficulty

class QuizGenerateResponse(BaseModel):
    questions: List[QuestionSchema]