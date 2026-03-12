from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.course_schema import CourseBootstrapOut


class DashboardBootstrapOut(BaseModel):
    student_id: UUID
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    available_subjects: list[Literal["math", "english", "civic"]] = Field(default_factory=list)
    active_subject: Literal["math", "english", "civic"] | None = None
    warmed_subjects: list[Literal["math", "english", "civic"]] = Field(default_factory=list)
    failed_subjects: list[Literal["math", "english", "civic"]] = Field(default_factory=list)
    course_bootstrap: CourseBootstrapOut | None = None
