from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy.orm import Session

from backend.repositories.tutor_session_repo import TutorSessionRepository
from backend.schemas.tutor_schema import (
    TutorPendingAssessmentOut,
    TutorQuickActionOut,
    TutorSessionBootstrapIn,
    TutorSessionBootstrapOut,
)
from backend.services.lesson_graph_service import lesson_graph_service
from backend.services.lesson_service import fetch_topic_lesson
from backend.services.tutor_assessment_service import TutorAssessmentService

BOOTSTRAP_CACHE_TTL_SECONDS = 30.0
_BOOTSTRAP_CACHE: dict[str, tuple[float, TutorSessionBootstrapOut]] = {}


class LessonExperienceService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = TutorSessionRepository(db)
        self.assessment_service = TutorAssessmentService(db)

    def _get_or_create_session(self, *, payload: TutorSessionBootstrapIn) -> tuple[UUID, bool]:
        if payload.session_id and self.session_repo.session_exists_for_student(
            session_id=payload.session_id,
            student_id=payload.student_id,
        ):
            return payload.session_id, False

        row = self.session_repo.create_session(
            student_id=payload.student_id,
            subject=payload.subject,
            term=int(payload.term),
        )
        return UUID(str(row["id"])), True

    @staticmethod
    def _cache_key(*, payload: TutorSessionBootstrapIn, session_id: UUID) -> str:
        return ":".join(
            [
                str(payload.student_id),
                payload.subject,
                payload.sss_level,
                str(payload.term),
                str(payload.topic_id),
                str(session_id),
            ]
        )

    @staticmethod
    def _read_cached_bootstrap(*, cache_key: str) -> TutorSessionBootstrapOut | None:
        entry = _BOOTSTRAP_CACHE.get(cache_key)
        if entry is None:
            return None
        created_at, payload = entry
        if (time.time() - created_at) > BOOTSTRAP_CACHE_TTL_SECONDS:
            _BOOTSTRAP_CACHE.pop(cache_key, None)
            return None
        return payload

    @staticmethod
    def _write_cached_bootstrap(*, cache_key: str, payload: TutorSessionBootstrapOut) -> TutorSessionBootstrapOut:
        _BOOTSTRAP_CACHE[cache_key] = (time.time(), payload)
        return payload

    @staticmethod
    def invalidate_session_cache(*, session_id: UUID) -> None:
        session_token = f":{session_id}"
        for key in [cache_key for cache_key in list(_BOOTSTRAP_CACHE.keys()) if cache_key.endswith(session_token)]:
            _BOOTSTRAP_CACHE.pop(key, None)

    @staticmethod
    def _suggested_actions(topic_title: str) -> list[TutorQuickActionOut]:
        return [
            TutorQuickActionOut(
                id="teach-simple",
                label="Explain Simpler",
                prompt=f"Teach {topic_title} like I am new to it and keep it step-by-step.",
                icon="sparkles",
                intent="teach",
            ),
            TutorQuickActionOut(
                id="real-life-example",
                label="Real-life Example",
                prompt=f"Give me one real-life example that makes {topic_title} easy to understand.",
                icon="lightbulb",
                intent="teach",
            ),
            TutorQuickActionOut(
                id="why-this-topic",
                label="Why This Topic?",
                prompt=f"Why am I learning {topic_title} now, and what does it unlock next?",
                icon="git-branch",
                intent="diagnose",
            ),
            TutorQuickActionOut(
                id="checkpoint",
                label="1-Min Checkpoint",
                prompt=f"Ask me one focused question on {topic_title}.",
                icon="target",
                intent="assessment_start",
            ),
            TutorQuickActionOut(
                id="prereq-bridge",
                label="Connect to Previous Topic",
                prompt=f"Bridge the prerequisite idea I need before mastering {topic_title}.",
                icon="route",
                intent="socratic",
            ),
            TutorQuickActionOut(
                id="common-mistake",
                label="Common Mistake",
                prompt=f"Show me a common mistake students make in {topic_title} and fix it.",
                icon="shield-alert",
                intent="diagnose",
            ),
            TutorQuickActionOut(
                id="waec-mode",
                label="WAEC Mode",
                prompt=f"Give me one WAEC-style coaching explanation for {topic_title}.",
                icon="graduation-cap",
                intent="exam-practice",
            ),
            TutorQuickActionOut(
                id="recap",
                label="Recap",
                prompt=f"Recap {topic_title} in three sharp points and one memory hook.",
                icon="notebook-pen",
                intent="recap",
            ),
        ]

    def bootstrap(self, payload: TutorSessionBootstrapIn) -> TutorSessionBootstrapOut:
        session_id, session_started = self._get_or_create_session(payload=payload)
        cache_key = self._cache_key(payload=payload, session_id=session_id)
        cached = self._read_cached_bootstrap(cache_key=cache_key)
        if cached is not None:
            if session_started:
                return cached.model_copy(update={"session_started": True, "session_id": session_id})
            return cached

        lesson = fetch_topic_lesson(
            db=self.db,
            topic_id=payload.topic_id,
            student_id=payload.student_id,
        )
        graph_context = lesson_graph_service.get_lesson_graph_context(
            self.db,
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=int(payload.term),
            topic_id=payload.topic_id,
        )
        why = lesson_graph_service.explain_why_this_topic(
            self.db,
            student_id=payload.student_id,
            subject=payload.subject,
            sss_level=payload.sss_level,
            term=int(payload.term),
            topic_id=payload.topic_id,
        )
        pending_state = self.assessment_service.get_pending_assessment(session_id=session_id)
        pending_assessment = None
        if pending_state is not None:
            pending_assessment = TutorPendingAssessmentOut(
                assessment_id=UUID(str(pending_state["assessment_id"])),
                question=str(pending_state.get("question") or ""),
                concept_id=str(pending_state.get("concept_id") or ""),
                concept_label=str(pending_state.get("concept_label") or ""),
                hint=str(pending_state.get("hint") or "").strip() or None,
                difficulty=str(pending_state.get("difficulty") or "").strip() or None,
            )

        greeting = (
            f"You are in {lesson.get('title')}. "
            f"Your weakest focus here is {graph_context.weakest_concepts[0].label if graph_context.weakest_concepts else 'the current lesson core idea'}, "
            "and the graph is showing what unlocks next."
        )
        bootstrap = TutorSessionBootstrapOut(
            session_id=session_id,
            session_started=session_started,
            greeting=greeting,
            topic_id=payload.topic_id,
            lesson=lesson,
            graph_context=graph_context,
            suggested_actions=self._suggested_actions(graph_context.topic_title),
            pending_assessment=pending_assessment,
            next_unlock=graph_context.next_unlock,
            why_this_topic=why.explanation,
            graph_nodes=graph_context.graph_nodes,
            graph_edges=graph_context.graph_edges,
            assessment_ready=bool(graph_context.current_concepts),
        )
        return self._write_cached_bootstrap(cache_key=cache_key, payload=bootstrap)


lesson_experience_service = LessonExperienceService
