from uuid import uuid4

from backend.schemas.course_schema import CourseBootstrapOut, CourseBootstrapTopicOut
from backend.services.course_experience_service import CourseExperienceService, _COURSE_BOOTSTRAP_CACHE


def test_course_bootstrap_cache_invalidation_is_scope_specific():
    _COURSE_BOOTSTRAP_CACHE.clear()
    student_id = uuid4()

    scoped_key = CourseExperienceService._cache_key(
        student_id=student_id,
        subject="math",
        sss_level="SSS2",
        term=2,
        mastery_signature="abc123",
    )
    other_key = CourseExperienceService._cache_key(
        student_id=student_id,
        subject="math",
        sss_level="SSS2",
        term=3,
        mastery_signature="def456",
    )

    payload = CourseBootstrapOut(
        student_id=student_id,
        subject="math",
        sss_level="SSS2",
        term=2,
        topics=[],
        next_step=None,
        recent_evidence=None,
        recommendation_story=None,
        map_error=None,
        warmed_topic_ids=[],
        cache_hit_topic_ids=[],
        failed_topic_ids=[],
    )
    CourseExperienceService._write_cached_bootstrap(cache_key=scoped_key, payload=payload)
    CourseExperienceService._write_cached_bootstrap(
        cache_key=other_key,
        payload=payload.model_copy(update={"term": 3}),
    )

    CourseExperienceService.invalidate_scope_cache(
        student_id=student_id,
        subject="math",
        sss_level="SSS2",
        term=2,
    )

    assert scoped_key not in _COURSE_BOOTSTRAP_CACHE
    assert other_key in _COURSE_BOOTSTRAP_CACHE
    _COURSE_BOOTSTRAP_CACHE.clear()


def test_candidate_prewarm_topic_ids_prefers_recommended_current_and_ready_topics():
    recommended_topic_id = uuid4()
    current_topic_id = uuid4()
    ready_topic_id = uuid4()
    locked_topic_id = uuid4()

    topics = [
        CourseBootstrapTopicOut(
            topic_id=str(current_topic_id),
            title="Current Topic",
            sss_level="SSS2",
            term=2,
            subject_id=str(uuid4()),
            lesson_ready=True,
            status="current",
        ),
        CourseBootstrapTopicOut(
            topic_id=str(ready_topic_id),
            title="Ready Topic",
            sss_level="SSS2",
            term=2,
            subject_id=str(uuid4()),
            lesson_ready=True,
            status="ready",
        ),
        CourseBootstrapTopicOut(
            topic_id=str(locked_topic_id),
            title="Locked Topic",
            sss_level="SSS2",
            term=2,
            subject_id=str(uuid4()),
            lesson_ready=False,
            status="locked",
        ),
    ]
    next_step = type("NextStep", (), {"recommended_topic_id": str(recommended_topic_id)})()

    candidate_ids = CourseExperienceService._candidate_prewarm_topic_ids(
        topics=topics,
        next_step=next_step,
    )

    assert candidate_ids == [recommended_topic_id, current_topic_id, ready_topic_id]
