from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.course_schema import CourseBootstrapTopicOut, CourseRecentEvidenceOut
from backend.schemas.learning_path_schema import PathNextOut
from backend.schemas.tutor_schema import TutorSessionBootstrapOut


class LessonCockpitBootstrapIn(BaseModel):
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topic_id: UUID
    session_id: UUID | None = None


class LessonCockpitBootstrapOut(BaseModel):
    student_id: UUID
    topic_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    topics: list[CourseBootstrapTopicOut] = Field(default_factory=list)
    next_step: PathNextOut | None = None
    recent_evidence: CourseRecentEvidenceOut | None = None
    map_error: str | None = None
    tutor_bootstrap: TutorSessionBootstrapOut
    warmed_topic_ids: list[str] = Field(default_factory=list)
    cache_hit_topic_ids: list[str] = Field(default_factory=list)
    failed_topic_ids: list[str] = Field(default_factory=list)
