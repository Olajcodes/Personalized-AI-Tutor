"""Release-gate validation checks for demo readiness.

This service is used by scripts/tests before a demo freeze to verify:
- required API routes are mounted
- critical tables are present
- minimum seed data exists for student/teacher/admin flows
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.main import app
from backend.models.lesson import Lesson
from backend.models.student import StudentProfile
from backend.models.subject import Subject
from backend.models.topic import Topic
from backend.models.user import User


REQUIRED_PUBLIC_PATHS = [
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/password",
    "/api/v1/students/profile/setup",
    "/api/v1/students/profile",
    "/api/v1/learning/activity/log",
    "/api/v1/learning/topics",
    "/api/v1/learning/topics/{topic_id}/lesson",
    "/api/v1/tutor/sessions/start",
    "/api/v1/tutor/chat",
    "/api/v1/learning/mastery",
    "/api/v1/teachers/classes",
    "/api/v1/admin/curriculum/upload",
    "/api/v1/admin/governance/metrics",
    "/api/v1/internal/rag/retrieve",
    "/api/v1/system/health",
]

REQUIRED_TABLES = [
    "users",
    "student_profiles",
    "learning_preferences",
    "subjects",
    "topics",
    "lessons",
    "activity_logs",
    "tutor_sessions",
    "quiz_attempts",
    "teacher_classes",
    "curriculum_versions",
    "curriculum_ingestion_jobs",
]


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


class DemoValidationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _check_required_routes() -> ValidationCheck:
        paths = set(app.openapi().get("paths", {}).keys())
        missing = sorted(path for path in REQUIRED_PUBLIC_PATHS if path not in paths)
        if missing:
            return ValidationCheck(
                name="routes-mounted",
                status="fail",
                detail=f"Missing required routes: {', '.join(missing)}",
            )
        return ValidationCheck(
            name="routes-mounted",
            status="pass",
            detail=f"All required routes present ({len(REQUIRED_PUBLIC_PATHS)}).",
        )

    def _check_required_tables(self) -> ValidationCheck:
        table_names = set(inspect(self.db.get_bind()).get_table_names())
        missing = sorted(name for name in REQUIRED_TABLES if name not in table_names)
        if missing:
            return ValidationCheck(
                name="schema-readiness",
                status="fail",
                detail=f"Missing required tables: {', '.join(missing)}",
            )
        return ValidationCheck(
            name="schema-readiness",
            status="pass",
            detail=f"All required tables present ({len(REQUIRED_TABLES)}).",
        )

    def _check_subject_seed(self) -> ValidationCheck:
        rows = self.db.execute(select(Subject.slug)).all()
        slugs = {row[0] for row in rows}
        required = {"math", "english", "civic"}
        missing = sorted(required - slugs)
        if missing:
            return ValidationCheck(
                name="subject-seed",
                status="fail",
                detail=f"Missing seeded subjects: {', '.join(missing)}",
            )
        return ValidationCheck(
            name="subject-seed",
            status="pass",
            detail="Core subjects are seeded (math, english, civic).",
        )

    def _check_topic_and_lesson_seed(self) -> ValidationCheck:
        approved_topics = self.db.scalar(select(func.count()).select_from(Topic).where(Topic.is_approved.is_(True))) or 0
        lessons = self.db.scalar(select(func.count()).select_from(Lesson)) or 0
        if approved_topics < 3 or lessons < 3:
            return ValidationCheck(
                name="curriculum-seed",
                status="fail",
                detail=f"Insufficient curriculum seed (approved_topics={approved_topics}, lessons={lessons}).",
            )
        return ValidationCheck(
            name="curriculum-seed",
            status="pass",
            detail=f"Curriculum seed ready (approved_topics={approved_topics}, lessons={lessons}).",
        )

    def _check_role_seed(self) -> ValidationCheck:
        role_counts = dict(self.db.execute(select(User.role, func.count()).group_by(User.role)).all())
        required_roles = {"student", "teacher", "admin"}
        missing = sorted(role for role in required_roles if int(role_counts.get(role, 0)) < 1)
        if missing:
            return ValidationCheck(
                name="role-seed",
                status="fail",
                detail=f"Missing required role users: {', '.join(missing)}",
            )
        return ValidationCheck(
            name="role-seed",
            status="pass",
            detail="At least one user exists for student, teacher, and admin roles.",
        )

    def _check_student_profiles(self) -> ValidationCheck:
        count = self.db.scalar(select(func.count()).select_from(StudentProfile)) or 0
        if count < 1:
            return ValidationCheck(
                name="student-profiles",
                status="fail",
                detail="No student profile records found.",
            )
        return ValidationCheck(
            name="student-profiles",
            status="pass",
            detail=f"Student profiles available ({count}).",
        )

    @staticmethod
    def _check_ai_core_health() -> ValidationCheck:
        if not settings.ai_core_base_url:
            return ValidationCheck(
                name="ai-core-health",
                status="warn",
                detail="AI_CORE_BASE_URL not configured; fallback mode may be used.",
            )
        try:
            response = httpx.get(
                f"{settings.ai_core_base_url.rstrip('/')}/health",
                timeout=settings.ai_core_timeout_seconds,
            )
            if response.status_code == 200:
                return ValidationCheck(
                    name="ai-core-health",
                    status="pass",
                    detail="ai-core health endpoint reachable.",
                )
            return ValidationCheck(
                name="ai-core-health",
                status="fail",
                detail=f"ai-core health returned HTTP {response.status_code}.",
            )
        except Exception as exc:
            return ValidationCheck(
                name="ai-core-health",
                status="fail",
                detail=f"ai-core health check failed: {exc}",
            )

    def validate(self) -> dict:
        checks = [
            self._check_required_routes(),
            self._check_required_tables(),
            self._check_subject_seed(),
            self._check_topic_and_lesson_seed(),
            self._check_role_seed(),
            self._check_student_profiles(),
            self._check_ai_core_health(),
        ]
        failures = [item for item in checks if item.status == "fail"]
        warnings = [item for item in checks if item.status == "warn"]
        return {
            "status": "fail" if failures else ("warn" if warnings else "pass"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(checks),
                "passed": len([item for item in checks if item.status == "pass"]),
                "warnings": len(warnings),
                "failed": len(failures),
            },
            "checks": [item.as_dict() for item in checks],
        }
