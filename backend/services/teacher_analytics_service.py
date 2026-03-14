from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from uuid import UUID

from backend.repositories.teacher_repo import TeacherRepository
from backend.schemas.teacher_schema import (
    CompletionDistributionOut,
    TeacherAlertOut,
    TeacherAlertsOut,
    TeacherClassDashboardOut,
    TeacherClassGraphOut,
    TeacherGraphEdgeOut,
    TeacherClassHeatmapOut,
    TeacherGraphConceptNodeOut,
    TeacherGraphMetricsOut,
    TeacherGraphSignalOut,
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
GRAPH_MASTERY_THRESHOLD = 0.7
GRAPH_WEAK_THRESHOLD = 0.5


class TeacherAnalyticsService:
    def __init__(self, repo: TeacherRepository):
        self.repo = repo

    @staticmethod
    def _readable_concept_label(concept_id: str | None, *, fallback: str | None = None) -> str:
        value = str(concept_id or "").strip()
        if not value:
            return str(fallback or "Concept").strip()
        token = value.rsplit(":", 1)[-1].strip()
        token = re.sub(r"-(\d+)$", "", token)
        token = re.sub(r"[_-]+", " ", token)
        token = re.sub(r"\s+", " ", token).strip()
        return token.title() if token else str(fallback or "Concept").strip()

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

    def get_class_graph_summary(self, *, teacher_id: UUID, class_id: UUID) -> TeacherClassGraphOut:
        self._require_teacher_user(teacher_id)
        teacher_class = self._require_teacher_class(teacher_id=teacher_id, class_id=class_id)

        heatmap_rows = self.repo.get_heatmap_points(
            class_id=class_id,
            subject=teacher_class.subject,
            term=teacher_class.term,
        )
        scope_rows = self.repo.get_scope_concept_rows(
            subject=teacher_class.subject,
            sss_level=teacher_class.sss_level,
            term=teacher_class.term,
        )

        heatmap_map = {
            str(row["concept_id"]): {
                "avg_score": float(row["avg_score"]),
                "student_count": int(row["student_count"]),
            }
            for row in heatmap_rows
        }
        concept_rows_by_id = {
            str(row["concept_id"]): row
            for row in scope_rows
            if str(row.get("concept_id") or "").strip()
        }

        nodes: list[TeacherGraphConceptNodeOut] = []
        edges: list[TeacherGraphEdgeOut] = []
        for concept_id, row in concept_rows_by_id.items():
            stat = heatmap_map.get(concept_id, {"avg_score": 0.0, "student_count": 0})
            prereq_ids = [item for item in list(row.get("prereq_concept_ids") or []) if item]
            blocking_prereqs = [
                prereq_id
                for prereq_id in prereq_ids
                if float(heatmap_map.get(prereq_id, {"avg_score": 0.0})["avg_score"]) < GRAPH_MASTERY_THRESHOLD
            ]
            avg_score = float(stat["avg_score"])
            student_count = int(stat["student_count"])

            if student_count <= 0:
                status = "unassessed"
                recommended_action = "Assign a checkpoint or quiz so this concept enters the graph."
            elif blocking_prereqs:
                status = "blocked"
                recommended_action = "Repair the weakest prerequisite before pushing this concept."
            elif avg_score < GRAPH_MASTERY_THRESHOLD:
                status = "needs_attention"
                recommended_action = "Strengthen this concept cluster with guided practice."
            else:
                status = "mastered"
                recommended_action = "Use this concept to unlock the next cluster."

            nodes.append(
                TeacherGraphConceptNodeOut(
                    concept_id=concept_id,
                    concept_label=self._readable_concept_label(concept_id, fallback=row.get("topic_title")),
                    topic_id=row.get("topic_id"),
                    topic_title=row.get("topic_title"),
                    avg_score=round(avg_score, 4),
                    student_count=student_count,
                    status=status,
                    prerequisite_labels=[
                        self._readable_concept_label(prereq_id, fallback=concept_rows_by_id.get(prereq_id, {}).get("topic_title"))
                        for prereq_id in prereq_ids
                    ],
                    blocking_prerequisite_labels=[
                        self._readable_concept_label(prereq_id, fallback=concept_rows_by_id.get(prereq_id, {}).get("topic_title"))
                        for prereq_id in blocking_prereqs
                    ],
                    recommended_action=recommended_action,
                )
            )
            for prereq_id in prereq_ids:
                if prereq_id not in concept_rows_by_id:
                    continue
                edges.append(
                    TeacherGraphEdgeOut(
                        source_concept_id=prereq_id,
                        target_concept_id=concept_id,
                        status="blocked" if prereq_id in blocking_prereqs else "ready",
                    )
                )

        blocked_nodes = sorted(
            [node for node in nodes if node.status == "blocked"],
            key=lambda item: (item.avg_score, item.concept_label),
        )
        weak_nodes = sorted(
            [node for node in nodes if node.status == "needs_attention"],
            key=lambda item: (item.avg_score, item.concept_label),
        )
        mastered_nodes = sorted(
            [node for node in nodes if node.status == "mastered"],
            key=lambda item: (-item.avg_score, item.concept_label),
        )
        unassessed_nodes = sorted(
            [node for node in nodes if node.status == "unassessed"],
            key=lambda item: (item.concept_label, item.topic_title or ""),
        )

        metrics = TeacherGraphMetricsOut(
            mapped_concepts=len(nodes),
            blocked_concepts=len(blocked_nodes),
            weak_concepts=len(weak_nodes),
            mastered_concepts=len(mastered_nodes),
            unassessed_concepts=len(unassessed_nodes),
        )

        if blocked_nodes:
            focus = blocked_nodes[0]
            graph_signal = TeacherGraphSignalOut(
                status="repair_prerequisite",
                headline=f"Repair {focus.blocking_prerequisite_labels[0]} before pushing {focus.concept_label}.",
                supporting_reason="The class is hitting a prerequisite barrier in the current graph scope.",
                focus_concept_label=focus.concept_label,
                blocking_prerequisite_label=focus.blocking_prerequisite_labels[0] if focus.blocking_prerequisite_labels else None,
                recommended_action="Revisit the blocker and assign a prerequisite-focused drill.",
            )
        elif weak_nodes:
            focus = weak_nodes[0]
            graph_signal = TeacherGraphSignalOut(
                status="strengthen_cluster",
                headline=f"Strengthen {focus.concept_label} before unlocking the next concept cluster.",
                supporting_reason="Prerequisites are mostly in place, but the active concept cluster is still below mastery.",
                focus_concept_label=focus.concept_label,
                blocking_prerequisite_label=None,
                recommended_action="Run a focused checkpoint or quiz on this concept.",
            )
        elif mastered_nodes:
            focus = mastered_nodes[0]
            graph_signal = TeacherGraphSignalOut(
                status="advance_class",
                headline=f"The class is ready to push beyond {focus.concept_label}.",
                supporting_reason="Current concept mastery is healthy enough to unlock the next lesson cluster.",
                focus_concept_label=focus.concept_label,
                blocking_prerequisite_label=None,
                recommended_action="Advance the class to the next mapped lesson and monitor the new weak node.",
            )
        else:
            graph_signal = TeacherGraphSignalOut(
                status="insufficient_data",
                headline="The class graph is still sparse.",
                supporting_reason="There is not enough mastery evidence yet to recommend the next graph move confidently.",
                focus_concept_label=None,
                blocking_prerequisite_label=None,
                recommended_action="Collect more quiz or tutor checkpoint evidence for this scope.",
            )

        return TeacherClassGraphOut(
            class_id=class_id,
            metrics=metrics,
            graph_signal=graph_signal,
            nodes=(blocked_nodes + weak_nodes + mastered_nodes + unassessed_nodes),
            edges=sorted(edges, key=lambda item: (item.status, item.target_concept_id, item.source_concept_id)),
            weakest_blockers=(blocked_nodes[:6] or weak_nodes[:6] or unassessed_nodes[:6]),
            ready_to_push=mastered_nodes[:6],
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
