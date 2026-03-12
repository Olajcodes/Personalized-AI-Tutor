from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from backend.schemas.lesson_cockpit_schema import LessonCockpitBootstrapIn, LessonCockpitBootstrapOut
from backend.schemas.tutor_schema import TutorSessionBootstrapIn
from backend.services.course_experience_service import CourseExperienceService
from backend.services.lesson_experience_service import LessonExperienceService


class LessonCockpitService:
    def __init__(self, db: Session):
        self.db = db
        self.course_service = CourseExperienceService(db)
        self.lesson_service = LessonExperienceService(db)

    def bootstrap(self, payload: LessonCockpitBootstrapIn) -> LessonCockpitBootstrapOut:
        course_bootstrap = self.course_service.bootstrap(
            student_id=payload.student_id,
            subject=payload.subject,
            term=int(payload.term),
        )
        tutor_bootstrap = self.lesson_service.bootstrap(
            TutorSessionBootstrapIn(
                student_id=payload.student_id,
                subject=payload.subject,
                sss_level=payload.sss_level,
                term=payload.term,
                topic_id=payload.topic_id,
                session_id=payload.session_id,
            )
        )

        course_topics = list(course_bootstrap.topics)
        current_index = next(
            (index for index, topic in enumerate(course_topics) if str(topic.topic_id) == str(payload.topic_id)),
            -1,
        )
        candidate_ids: list[UUID] = []

        def _append_topic(topic_id: str | None) -> None:
            if not topic_id:
                return
            try:
                parsed = UUID(str(topic_id))
            except (TypeError, ValueError):
                return
            if parsed == payload.topic_id:
                return
            if parsed in candidate_ids:
                return
            candidate_ids.append(parsed)

        if current_index >= 0:
            if current_index + 1 < len(course_topics):
                _append_topic(course_topics[current_index + 1].topic_id)
            if current_index - 1 >= 0:
                _append_topic(course_topics[current_index - 1].topic_id)

        _append_topic(course_bootstrap.next_step.recommended_topic_id if course_bootstrap.next_step else None)
        _append_topic(tutor_bootstrap.next_unlock.topic_id if tutor_bootstrap.next_unlock else None)
        weakest_prereq_topic_id = next(
            (item.topic_id for item in tutor_bootstrap.graph_context.prerequisite_concepts if item.topic_id),
            None,
        )
        _append_topic(weakest_prereq_topic_id)

        prewarm = LessonExperienceService.prewarm_topics(
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=int(payload.term),
            topic_ids=candidate_ids,
        )

        return LessonCockpitBootstrapOut(
            student_id=payload.student_id,
            topic_id=payload.topic_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=payload.term,
            topics=course_topics,
            next_step=course_bootstrap.next_step,
            map_error=course_bootstrap.map_error,
            tutor_bootstrap=tutor_bootstrap,
            warmed_topic_ids=prewarm["warmed_topic_ids"],
            cache_hit_topic_ids=prewarm["cache_hit_topic_ids"],
            failed_topic_ids=prewarm["failed_topic_ids"],
        )
