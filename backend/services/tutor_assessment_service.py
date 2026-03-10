from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.repositories.activity_repo import ActivityRepository
from backend.repositories.tutor_session_repo import TutorSessionRepository
from backend.schemas.activity_schema import ActivityLogCreate
from backend.schemas.internal_graph_schema import ConceptUpdateIn, InternalGraphUpdateIn
from backend.schemas.tutor_schema import (
    TutorAssessmentStartIn,
    TutorAssessmentStartOut,
    TutorAssessmentSubmitIn,
    TutorAssessmentSubmitOut,
)
from backend.services.activity_service import ActivityService
from backend.services.graph_client_service import GraphClientValidationError, graph_client_service
from backend.services.tutor_orchestration_service import (
    TutorOrchestrationService,
    TutorProviderUnavailableError,
)

_ASSESSMENT_PREFIX = "TUTOR_ASSESSMENT_STATE::"


class TutorAssessmentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TutorSessionRepository(db)
        self.orchestration = TutorOrchestrationService()
        self.activity_service = ActivityService(ActivityRepository(db))

    @staticmethod
    def _encode_state(payload: dict) -> str:
        return _ASSESSMENT_PREFIX + json.dumps(payload, ensure_ascii=True)

    @staticmethod
    def _decode_state(content: str) -> dict | None:
        value = str(content or "")
        if not value.startswith(_ASSESSMENT_PREFIX):
            return None
        try:
            parsed = json.loads(value[len(_ASSESSMENT_PREFIX) :])
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def _find_pending_state(self, *, session_id: UUID, assessment_id: UUID) -> tuple[UUID, dict] | None:
        history = self.repo.get_session_history(session_id=session_id)
        for row in reversed(history):
            state = self._decode_state(str(row.get("content") or ""))
            if not state:
                continue
            if str(state.get("assessment_id") or "") != str(assessment_id):
                continue
            if str(state.get("status") or "").strip().lower() != "pending":
                continue
            return UUID(str(row["id"])), state
        return None

    def get_pending_assessment(self, *, session_id: UUID) -> dict | None:
        history = self.repo.get_session_history(session_id=session_id)
        for row in reversed(history):
            state = self._decode_state(str(row.get("content") or ""))
            if not state:
                continue
            if str(state.get("status") or "").strip().lower() != "pending":
                continue
            return state
        return None

    @staticmethod
    def _assessment_weight(score: float) -> tuple[bool, float]:
        if score >= 0.8:
            return True, 0.12
        if score >= 0.55:
            return True, 0.05
        return False, 0.04

    async def start_assessment(self, payload: TutorAssessmentStartIn) -> TutorAssessmentStartOut:
        ai_out = await self.orchestration.assessment_start(payload)
        assessment_id = uuid4()
        state = {
            "assessment_id": str(assessment_id),
            "topic_id": str(payload.topic_id),
            "concept_id": ai_out.concept_id,
            "concept_label": ai_out.concept_label,
            "question": ai_out.question,
            "ideal_answer": ai_out.ideal_answer,
            "hint": ai_out.hint,
            "difficulty": payload.difficulty,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.add_message(
            session_id=payload.session_id,
            role="system",
            content=self._encode_state(state),
        )
        self.repo.add_message(
            session_id=payload.session_id,
            role="assistant",
            content=f"Check question: {ai_out.question}",
        )
        return ai_out.model_copy(update={"assessment_id": assessment_id})

    async def submit_assessment(self, payload: TutorAssessmentSubmitIn) -> TutorAssessmentSubmitOut:
        match = self._find_pending_state(session_id=payload.session_id, assessment_id=payload.assessment_id)
        if match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending tutor assessment not found for this session.",
            )
        message_id, state = match

        self.repo.add_message(session_id=payload.session_id, role="student", content=payload.answer)
        ai_out = await self.orchestration.assessment_submit(
            payload,
            question=str(state.get("question") or ""),
            concept_id=str(state.get("concept_id") or ""),
            concept_label=str(state.get("concept_label") or ""),
            ideal_answer=str(state.get("ideal_answer") or ""),
        )

        is_positive, weight_change = self._assessment_weight(ai_out.score)
        mastery_updated = False
        new_mastery: float | None = None
        try:
            graph_out = graph_client_service.push_mastery_update(
                self.db,
                payload=InternalGraphUpdateIn(
                    student_id=payload.student_id,
                    quiz_id=None,
                    attempt_id=None,
                    subject=payload.subject,
                    sss_level=payload.sss_level,
                    term=payload.term,
                    timestamp=datetime.now(timezone.utc),
                    source="practice",
                    concept_breakdown=[
                        ConceptUpdateIn(
                            concept_id=ai_out.concept_id,
                            is_correct=is_positive,
                            weight_change=weight_change,
                        )
                    ],
                ),
            )
            mastery_updated = bool(graph_out.success)
            new_mastery = float(graph_out.new_mastery) if graph_out.new_mastery is not None else None
        except GraphClientValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        activity = ActivityLogCreate(
            student_id=payload.student_id,
            subject=payload.subject,
            term=payload.term,
            event_type="mastery_check_done",
            ref_id=str(payload.assessment_id),
            duration_seconds=0,
        )
        self.activity_service.log_activity(activity)

        resolved_state = dict(state)
        resolved_state.update(
            {
                "status": "answered",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "student_answer": payload.answer,
                "score": ai_out.score,
                "is_correct": ai_out.is_correct,
                "mastery_updated": mastery_updated,
                "new_mastery": new_mastery,
                "ideal_answer": ai_out.ideal_answer,
            }
        )
        self.repo.update_message_content(message_id=message_id, content=self._encode_state(resolved_state))
        self.repo.add_message(session_id=payload.session_id, role="assistant", content=ai_out.feedback)
        return ai_out.model_copy(
            update={
                "assessment_id": payload.assessment_id,
                "mastery_updated": mastery_updated,
                "new_mastery": new_mastery,
                "actions": list(ai_out.actions) + ["MASTERED_CHECK_RECORDED" if mastery_updated else "MASTERED_CHECK_SKIPPED"],
            }
        )
