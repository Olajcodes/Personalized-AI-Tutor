from uuid import uuid4

from backend.schemas.course_schema import CourseBootstrapOut
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
