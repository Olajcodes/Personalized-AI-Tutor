from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from backend.services.teacher_analytics_service import TeacherAnalyticsService


class FakeTeacherAnalyticsRepo:
    def __init__(self):
        self.teacher_id = uuid4()
        self.class_id = uuid4()
        self.student_a = uuid4()
        self.student_b = uuid4()
        self.users = {
            self.teacher_id: SimpleNamespace(id=self.teacher_id, role="teacher", is_active=True),
            self.student_a: SimpleNamespace(id=self.student_a, role="student", is_active=True),
            self.student_b: SimpleNamespace(id=self.student_b, role="student", is_active=True),
        }
        self.teacher_class = SimpleNamespace(
            id=self.class_id,
            teacher_id=self.teacher_id,
            subject="math",
            sss_level="SSS2",
            term=1,
        )

    def get_user(self, user_id):
        return self.users.get(user_id)

    def get_teacher_class(self, *, teacher_id, class_id):
        if teacher_id == self.teacher_id and class_id == self.class_id:
            return self.teacher_class
        return None

    def get_active_student_ids(self, *, class_id):
        return [self.student_a, self.student_b]

    def get_recent_activity_stats(self, *, class_id, subject, term, since):
        return {
            self.student_a: {
                "event_count": 3,
                "duration_seconds": 300,
                "quiz_submitted_count": 1,
                "lesson_viewed_count": 2,
            },
            self.student_b: {
                "event_count": 0,
                "duration_seconds": 0,
                "quiz_submitted_count": 0,
                "lesson_viewed_count": 0,
            },
        }

    def get_avg_mastery_by_student(self, *, class_id, subject, term):
        return {self.student_a: 0.8, self.student_b: 0.25}

    def get_heatmap_points(self, *, class_id, subject, term):
        return [
            {"concept_id": "math:sss2:t1:fractions", "avg_score": 0.2, "student_count": 2},
            {"concept_id": "math:sss2:t1:ratio", "avg_score": 0.7, "student_count": 1},
        ]

    def get_scope_concept_rows(self, *, subject, sss_level, term):
        return [
            {
                "concept_id": "math:sss2:t1:fractions",
                "prereq_concept_ids": ["math:sss2:t1:number-sense"],
                "topic_id": uuid4(),
                "topic_title": "Fractions",
            },
            {
                "concept_id": "math:sss2:t1:number-sense",
                "prereq_concept_ids": [],
                "topic_id": uuid4(),
                "topic_title": "Number Sense",
            },
            {
                "concept_id": "math:sss2:t1:ratio",
                "prereq_concept_ids": [],
                "topic_id": uuid4(),
                "topic_title": "Ratio",
            },
        ]

    def get_negative_mastery_delta_by_student(self, *, class_id, subject, term, since):
        return {self.student_a: -0.12}

    def get_low_mastery_students(self, *, class_id, subject, term, threshold):
        return {self.student_b: 0.25}

    def get_student_timeline(self, *, class_id, student_id, limit):
        now = datetime.now(timezone.utc)
        return [
            {
                "event_type": "activity",
                "occurred_at": now - timedelta(hours=1),
                "details": {"activity_type": "lesson_viewed"},
            },
            {
                "event_type": "mastery_update",
                "occurred_at": now - timedelta(hours=2),
                "details": {"source": "practice", "updated_concepts": 2},
            },
        ]


def test_teacher_analytics_dashboard_metrics():
    repo = FakeTeacherAnalyticsRepo()
    service = TeacherAnalyticsService(repo)

    out = service.get_class_dashboard(teacher_id=repo.teacher_id, class_id=repo.class_id)
    assert out.total_students == 2
    assert out.active_students_7d == 1
    assert out.avg_study_time_seconds_7d == 150
    assert out.avg_mastery_score == 0.525
    assert out.completion_distribution.completed == 1
    assert out.completion_distribution.no_activity == 1


def test_teacher_analytics_heatmap_points():
    repo = FakeTeacherAnalyticsRepo()
    service = TeacherAnalyticsService(repo)

    out = service.get_class_heatmap(teacher_id=repo.teacher_id, class_id=repo.class_id)
    assert out.class_id == repo.class_id
    assert len(out.points) == 2
    assert out.points[0].concept_id == "math:sss2:t1:fractions"


def test_teacher_analytics_graph_summary_prioritises_blockers():
    repo = FakeTeacherAnalyticsRepo()
    service = TeacherAnalyticsService(repo)

    out = service.get_class_graph_summary(teacher_id=repo.teacher_id, class_id=repo.class_id)

    assert out.class_id == repo.class_id
    assert out.metrics.mapped_concepts == 3
    assert out.metrics.blocked_concepts >= 1
    assert out.graph_signal.status == "repair_prerequisite"
    assert len(out.nodes) == 3
    assert any(edge.target_concept_id == "math:sss2:t1:fractions" for edge in out.edges)
    assert out.weakest_blockers[0].concept_label in {"Fractions", "Number Sense"}


def test_teacher_analytics_alerts_include_expected_types():
    repo = FakeTeacherAnalyticsRepo()
    service = TeacherAnalyticsService(repo)

    out = service.get_class_alerts(teacher_id=repo.teacher_id, class_id=repo.class_id)
    kinds = {alert.alert_type for alert in out.alerts}
    assert "inactivity" in kinds
    assert "rapid_decline" in kinds
    assert "prereq_failure" in kinds


def test_teacher_analytics_student_timeline_mapping():
    repo = FakeTeacherAnalyticsRepo()
    service = TeacherAnalyticsService(repo)

    out = service.get_student_timeline(
        teacher_id=repo.teacher_id,
        class_id=repo.class_id,
        student_id=repo.student_a,
        limit=20,
    )
    assert out.student_id == repo.student_a
    assert len(out.timeline) == 2
    assert out.timeline[0].event_type in {"activity", "mastery_update"}
