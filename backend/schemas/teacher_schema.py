from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Subject = Literal["math", "english", "civic"]
SSSLevel = Literal["SSS1", "SSS2", "SSS3"]
AssignmentType = Literal["topic", "quiz", "revision"]
InterventionType = Literal["note", "flag", "support_plan", "parent_contact"]
Severity = Literal["low", "medium", "high"]


class TeacherClassCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    subject: Subject
    sss_level: SSSLevel
    term: Literal[1, 2, 3]


class TeacherClassOut(BaseModel):
    id: UUID
    teacher_id: UUID
    name: str
    description: str | None = None
    subject: Subject
    sss_level: SSSLevel
    term: Literal[1, 2, 3]
    is_active: bool
    enrolled_count: int = 0
    created_at: datetime
    updated_at: datetime


class TeacherClassListOut(BaseModel):
    classes: list[TeacherClassOut]


class TeacherClassEnrollIn(BaseModel):
    student_ids: list[UUID] = Field(min_length=1, max_length=500)


class TeacherClassEnrollOut(BaseModel):
    class_id: UUID
    enrolled_student_ids: list[UUID]
    already_enrolled_student_ids: list[UUID]
    total_enrolled: int


class CompletionDistributionOut(BaseModel):
    completed: int = 0
    in_progress: int = 0
    no_activity: int = 0


class TeacherClassDashboardOut(BaseModel):
    class_id: UUID
    total_students: int
    active_students_7d: int
    avg_study_time_seconds_7d: int
    avg_mastery_score: float
    completion_distribution: CompletionDistributionOut


class TeacherHeatmapPointOut(BaseModel):
    concept_id: str
    avg_score: float
    student_count: int


class TeacherClassHeatmapOut(BaseModel):
    class_id: UUID
    points: list[TeacherHeatmapPointOut]


class TeacherGraphMetricsOut(BaseModel):
    mapped_concepts: int = 0
    blocked_concepts: int = 0
    weak_concepts: int = 0
    mastered_concepts: int = 0
    unassessed_concepts: int = 0


class TeacherGraphConceptNodeOut(BaseModel):
    concept_id: str
    concept_label: str
    topic_id: UUID | None = None
    topic_title: str | None = None
    avg_score: float
    student_count: int = 0
    status: Literal["blocked", "needs_attention", "mastered", "unassessed"]
    prerequisite_labels: list[str] = Field(default_factory=list)
    blocking_prerequisite_labels: list[str] = Field(default_factory=list)
    recommended_action: str


class TeacherGraphSignalOut(BaseModel):
    status: Literal["repair_prerequisite", "strengthen_cluster", "advance_class", "insufficient_data"]
    headline: str
    supporting_reason: str
    focus_concept_label: str | None = None
    blocking_prerequisite_label: str | None = None
    recommended_action: str


class TeacherClassGraphOut(BaseModel):
    class_id: UUID
    metrics: TeacherGraphMetricsOut
    graph_signal: TeacherGraphSignalOut
    weakest_blockers: list[TeacherGraphConceptNodeOut] = Field(default_factory=list)
    ready_to_push: list[TeacherGraphConceptNodeOut] = Field(default_factory=list)


class TeacherAlertOut(BaseModel):
    alert_type: Literal["inactivity", "rapid_decline", "prereq_failure"]
    severity: Severity
    student_id: UUID
    message: str
    generated_at: datetime


class TeacherAlertsOut(BaseModel):
    class_id: UUID
    alerts: list[TeacherAlertOut]


class TeacherTimelineEventOut(BaseModel):
    event_type: str
    occurred_at: datetime
    details: dict


class TeacherStudentTimelineOut(BaseModel):
    class_id: UUID
    student_id: UUID
    timeline: list[TeacherTimelineEventOut]


class TeacherAssignmentCreateIn(BaseModel):
    class_id: UUID | None = None
    student_id: UUID | None = None
    assignment_type: AssignmentType
    ref_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    instructions: str | None = Field(default=None, max_length=2000)
    subject: Subject
    sss_level: SSSLevel
    term: Literal[1, 2, 3]
    due_at: datetime | None = None


class TeacherAssignmentOut(BaseModel):
    id: UUID
    teacher_id: UUID
    class_id: UUID | None = None
    student_id: UUID | None = None
    assignment_type: AssignmentType
    ref_id: str
    title: str
    instructions: str | None = None
    subject: Subject
    sss_level: SSSLevel
    term: Literal[1, 2, 3]
    due_at: datetime | None = None
    status: Literal["assigned", "completed", "cancelled"]
    created_at: datetime
    updated_at: datetime


class TeacherInterventionCreateIn(BaseModel):
    class_id: UUID | None = None
    student_id: UUID
    intervention_type: InterventionType
    severity: Severity = "medium"
    subject: Subject
    sss_level: SSSLevel
    term: Literal[1, 2, 3]
    notes: str = Field(min_length=1, max_length=2000)
    action_plan: str | None = Field(default=None, max_length=2000)


class TeacherInterventionOut(BaseModel):
    id: UUID
    teacher_id: UUID
    class_id: UUID | None = None
    student_id: UUID
    intervention_type: InterventionType
    severity: Severity
    subject: Subject
    sss_level: SSSLevel
    term: Literal[1, 2, 3]
    notes: str
    action_plan: str | None = None
    status: Literal["open", "resolved", "dismissed"]
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
