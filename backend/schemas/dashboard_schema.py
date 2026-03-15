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


class StudentExportSectionOut(BaseModel):
    title: str
    items: list[str] = Field(default_factory=list)


class StudentPathBriefingOut(BaseModel):
    export_kind: Literal["student_path_briefing"] = "student_path_briefing"
    student_id: UUID
    subject: Literal["math", "english", "civic"]
    sss_level: Literal["SSS1", "SSS2", "SSS3"]
    term: Literal[1, 2, 3]
    title: str
    subtitle: str
    generated_at: str
    file_name: str
    markdown: str
    sections: list[StudentExportSectionOut] = Field(default_factory=list)
