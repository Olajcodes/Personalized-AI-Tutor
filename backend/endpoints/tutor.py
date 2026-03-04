"""Tutor AI endpoints.

Public endpoints for tutor chat and guided assistance modes:
- chat
- hint
- explain mistake
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.repositories.tutor_session_repo import TutorSessionRepository
from backend.schemas.internal_graph_schema import ConceptUpdateIn, InternalGraphUpdateIn
from backend.schemas.tutor_schema import (
    TutorChatIn,
    TutorChatOut,
    TutorExplainMistakeIn,
    TutorExplainMistakeOut,
    TutorHintIn,
    TutorHintOut,
)
from backend.services.tutor_orchestration_service import (
    TutorOrchestrationService,
    TutorProviderUnavailableError,
)
from backend.services.graph_client_service import graph_client_service

router = APIRouter(prefix="/tutor", tags=["Tutor AI"])
logger = logging.getLogger(__name__)


def _service() -> TutorOrchestrationService:
    return TutorOrchestrationService()


def _session_repo(db: Session) -> TutorSessionRepository:
    return TutorSessionRepository(db)


def _apply_chat_mastery_update(db: Session, payload: TutorChatIn) -> None:
    """Best-effort mastery update from tutor engagement in scoped topic."""
    if payload.topic_id is None:
        return

    update_payload = InternalGraphUpdateIn(
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
                concept_id=str(payload.topic_id),
                is_correct=True,
                weight_change=0.02,
            )
        ],
    )
    try:
        graph_client_service.push_mastery_update(db, payload=update_payload)
    except Exception as exc:
        logger.warning("Tutor chat mastery update skipped: %s", exc)


@router.post("/chat", response_model=TutorChatOut, status_code=status.HTTP_200_OK)
async def tutor_chat(
    payload: TutorChatIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Main tutor chat endpoint for guided teaching responses.

    Validates student identity, verifies session ownership, and persists
    student/assistant messages into tutor session history.
    """
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )

    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")

    repo.add_message(session_id=payload.session_id, role="student", content=payload.message)

    try:
        response = await _service().chat(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))

    assistant_message = (
        response.assistant_message
        if hasattr(response, "assistant_message")
        else str(response.get("assistant_message", ""))
    )
    repo.add_message(session_id=payload.session_id, role="assistant", content=assistant_message)
    _apply_chat_mastery_update(db, payload)
    return response


@router.post("/hint", response_model=TutorHintOut, status_code=status.HTTP_200_OK)
async def tutor_hint(
    payload: TutorHintIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return a guided hint for an in-progress quiz question.

    If a session id is supplied, ownership is validated before generating hint.
    """
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )

    if payload.session_id is not None:
        repo = _session_repo(db)
        if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")

    try:
        return await _service().hint(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/explain-mistake", response_model=TutorExplainMistakeOut, status_code=status.HTTP_200_OK)
async def tutor_explain_mistake(
    payload: TutorExplainMistakeIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Explain why a student's answer is incorrect with remediation guidance."""
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )

    if payload.session_id is not None:
        repo = _session_repo(db)
        if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")

    try:
        return await _service().explain_mistake(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
