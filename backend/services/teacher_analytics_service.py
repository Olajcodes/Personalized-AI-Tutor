from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from backend.repositories.teacher_repo import TeacherRepository
from backend.schemas.teacher_schema import (
    CompletionDistributionOut,
    TeacherAlertOut,
    TeacherAlertsOut,
    TeacherClassDashboardOut,
    TeacherClassHeatmapOut,
    TeacherHeatmapPointOut,
    TeacherStudentTimelineOut,
    TeacherTimelineEventOut,
)
from backend.services.teacher_service import (
    TeacherServiceNotFoundError,
    TeacherServiceUnauthorizedError,
)


INACTIVITY_DAYS = 7
RAPID_DECLINE_DAYS = 14
RAPID_DECLINE_HIGH_THRESHOLD = -0.2
RAPID_DECLINE_MEDIUM_THRESHOLD = -0.1
LOW_MASTERY_THRESHOLD = 0.4
LOW_MASTERY_HIGH_SEVERITY = 0.3


class TeacherAnalyticsService:
    def __init__(self, repo: TeacherRepository):
        self.repo = repo

    def _require_teacher_user(self, teacher_id: UUID):
        user = self.repo.get_user(teacher_id)
        if not user:
            raise TeacherServiceNotFoundError("Teacher user not found.")
        if not user.is_active:
            raise TeacherServiceUnauthorizedError("Teacher account is inactive.")
        if user.role not in {"teacher", "admin"}:
            raise TeacherServiceUnauthorizedError("Only teacher/admin role can access teacher analytics.")
        return user

    def _require_teacher_class(self, *, teacher_id: UUID, class_id: UUID):
        row = self.repo.get_teacher_class(teacher_id=teacher_id, class_id=class_id)
        if not row:
            raise TeacherServiceNotFoundError("Class not found for this teacher.")
        return row

    def get_class_dashboard(self, *, teacher_id: UUID, class_id: UUID) -> TeacherClassDashboardOut:
        self._require_teacher_user(teacher_id)
        teacher_class = self._require_teacher_class(teacher_id=teacher_id, class_id=class_id)

        student_ids = self.repo.get_active_student_ids(class_id=class_id)
        total_students = len(student_ids)
        if total_students == 0:
            return TeacherClassDashboardOut(
                class_id=class_id,
                total_students=0,
                active_students_7d=0,
                avg_study_time_seconds_7d=0,
                avg_mastery_score=0.0,
                completion_distribution=CompletionDistributionOut(
                    completed=0,
                    in_progress=0,
                    no_activity=0,
                ),
            )

        since = datetime.now(timezone.utc) - timedelta(days=INACTIVITY_DAYS)
        activity_stats = self.repo.get_recent_activity_stats(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
            since=since,
        )

        active_students_7d = sum(1 for student_id in student_ids if activity_stats.get(student_id, {}).get("event_count", 0) > 0)
        total_duration = sum(activity_stats.get(student_id, {}).get("duration_seconds", 0) for student_id in student_ids)
        avg_study_time = int(total_duration / total_students) if total_students else 0

        mastery_map = self.repo.get_avg_mastery_by_student(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
        )
        avg_mastery_score = round(sum(mastery_map.values()) / len(mastery_map), 4) if mastery_map else 0.0

        completed = 0
        in_progress = 0
        no_activity = 0
        for student_id in student_ids:
            stats = activity_stats.get(student_id)
            if not stats or stats["event_count"] == 0:
                no_activity += 1
                continue
            if stats["quiz_submitted_count"] > 0 and stats["lesson_viewed_count"] > 0:
                completed += 1
            else:
                in_progress += 1

        return TeacherClassDashboardOut(
            class_id=class_id,
            total_students=total_students,
            active_students_7d=active_students_7d,
            avg_study_time_seconds_7d=avg_study_time,
            avg_mastery_score=avg_mastery_score,
            completion_distribution=CompletionDistributionOut(
                completed=completed,
                in_progress=in_progress,
                no_activity=no_activity,
            ),
        )

    def get_class_heatmap(self, *, teacher_id: UUID, class_id: UUID) -> TeacherClassHeatmapOut:
        self._require_teacher_user(teacher_id)
        teacher_class = self._require_teacher_class(teacher_id=teacher_id, class_id=class_id)

        points = self.repo.get_heatmap_points(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
        )
        return TeacherClassHeatmapOut(
            class_id=class_id,
            points=[
                TeacherHeatmapPointOut(
                    concept_id=row["concept_id"],
                    avg_score=round(float(row["avg_score"]), 4),
                    student_count=int(row["student_count"]),
                )
                for row in points
            ],
        )

    def get_class_alerts(self, *, teacher_id: UUID, class_id: UUID) -> TeacherAlertsOut:
        self._require_teacher_user(teacher_id)
        teacher_class = self._require_teacher_class(teacher_id=teacher_id, class_id=class_id)
        now = datetime.now(timezone.utc)

        student_ids = self.repo.get_active_student_ids(class_id=class_id)
        if not student_ids:
            return TeacherAlertsOut(class_id=class_id, alerts=[])

        alerts: dict[tuple[str, UUID], TeacherAlertOut] = {}

        inactivity_since = now - timedelta(days=INACTIVITY_DAYS)
        activity_stats = self.repo.get_recent_activity_stats(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
            since=inactivity_since,
        )
        for student_id in student_ids:
            if activity_stats.get(student_id, {}).get("event_count", 0) == 0:
                alerts[("inactivity", student_id)] = TeacherAlertOut(
                    alert_type="inactivity",
                    severity="medium",
                    student_id=student_id,
                    message=f"No learning activity in the last {INACTIVITY_DAYS} days.",
                    generated_at=now,
                )

        decline_since = now - timedelta(days=RAPID_DECLINE_DAYS)
        decline_totals = self.repo.get_negative_mastery_delta_by_student(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
            since=decline_since,
        )
        for student_id, total_delta in decline_totals.items():
            if total_delta <= RAPID_DECLINE_HIGH_THRESHOLD:
                severity = "high"
            elif total_delta <= RAPID_DECLINE_MEDIUM_THRESHOLD:
                severity = "medium"
            else:
                continue
            alerts[("rapid_decline", student_id)] = TeacherAlertOut(
                alert_type="rapid_decline",
                severity=severity,
                student_id=student_id,
                message=f"Mastery trend declined by {round(total_delta, 3)} in the last {RAPID_DECLINE_DAYS} days.",
                generated_at=now,
            )

        low_mastery = self.repo.get_low_mastery_students(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
            threshold=LOW_MASTERY_THRESHOLD,
        )
        for student_id, avg_score in low_mastery.items():
            severity = "high" if avg_score < LOW_MASTERY_HIGH_SEVERITY else "medium"
            alerts[("prereq_failure", student_id)] = TeacherAlertOut(
                alert_type="prereq_failure",
                severity=severity,
                student_id=student_id,
                message=f"Low foundational mastery detected (avg score {round(avg_score, 3)}).",
                generated_at=now,
            )

        sorted_alerts = sorted(
            alerts.values(),
            key=lambda row: (row.severity == "high", row.generated_at),
            reverse=True,
        )
        return TeacherAlertsOut(class_id=class_id, alerts=sorted_alerts)

    def get_student_timeline(
        self,
        *,
        teacher_id: UUID,
        class_id: UUID,
        student_id: UUID,
        limit: int = 50,
    ) -> TeacherStudentTimelineOut:
        self._require_teacher_user(teacher_id)
        self._require_teacher_class(teacher_id=teacher_id, class_id=class_id)

        student_user = self.repo.get_user(student_id)
        if not student_user or student_user.role != "student":
            raise TeacherServiceNotFoundError("Student not found.")

        timeline = self.repo.get_student_timeline(class_id=class_id, student_id=student_id, limit=limit)
        return TeacherStudentTimelineOut(
            class_id=class_id,
            student_id=student_id,
            timeline=[
                TeacherTimelineEventOut(
                    event_type=item["event_type"],
                    occurred_at=item["occurred_at"],
                    details=item["details"],
                )
                for item in timeline
            ],
        )
