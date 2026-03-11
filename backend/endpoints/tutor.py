"""Tutor AI endpoints.

Public endpoints for tutor chat and guided assistance modes:
- chat
- session bootstrap
- hint
- explain mistake
"""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.repositories.tutor_session_repo import TutorSessionRepository
from backend.schemas.tutor_schema import (
    TutorAssessmentStartIn,
    TutorAssessmentStartOut,
    TutorAssessmentSubmitIn,
    TutorAssessmentSubmitOut,
    TutorChatIn,
    TutorChatOut,
    TutorDrillIn,
    TutorExplainMistakeIn,
    TutorExplainMistakeOut,
    TutorHintIn,
    TutorHintOut,
    TutorPrereqBridgeIn,
    TutorRecapIn,
    TutorSessionBootstrapIn,
    TutorSessionBootstrapOut,
    TutorStudyPlanIn,
)
from backend.services.lesson_experience_service import LessonExperienceService
from backend.services.tutor_assessment_service import TutorAssessmentService
from backend.services.tutor_orchestration_service import (
    TutorOrchestrationService,
    TutorProviderUnavailableError,
)

router = APIRouter(prefix="/tutor", tags=["Tutor AI"])
logger = logging.getLogger(__name__)


def _service() -> TutorOrchestrationService:
    return TutorOrchestrationService()


def _session_repo(db: Session) -> TutorSessionRepository:
    return TutorSessionRepository(db)


def _assessment_service(db: Session) -> TutorAssessmentService:
    return TutorAssessmentService(db)


def _lesson_experience_service(db: Session) -> LessonExperienceService:
    return LessonExperienceService(db)


@router.post("/session/bootstrap", response_model=TutorSessionBootstrapOut, status_code=status.HTTP_200_OK)
def tutor_session_bootstrap(
    payload: TutorSessionBootstrapIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )
    try:
        response = _lesson_experience_service(db).bootstrap(payload)
        warm_topic_ids: list[UUID] = []
        if response.next_unlock and response.next_unlock.topic_id:
            try:
                warm_topic_ids.append(UUID(str(response.next_unlock.topic_id)))
            except Exception:
                pass
        weak_prereq_topic_id = next(
            (item.topic_id for item in response.graph_context.prerequisite_concepts if item.topic_id),
            None,
        )
        if weak_prereq_topic_id:
            try:
                warm_topic_ids.append(UUID(str(weak_prereq_topic_id)))
            except Exception:
                pass
        if warm_topic_ids:
            background_tasks.add_task(
                LessonExperienceService.prewarm_related_topics,
                student_id=payload.student_id,
                subject=payload.subject,
                sss_level=payload.sss_level,
                term=int(payload.term),
                topic_ids=warm_topic_ids,
            )
        return response
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


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
    logger.info(
        "Tutor chat completed without direct mastery write; awaiting evidence-based assessment flow. student_id=%s session_id=%s topic_id=%s",
        payload.student_id,
        payload.session_id,
        payload.topic_id,
    )
    return response


@router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def tutor_chat_stream(
    payload: TutorChatIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )

    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")

    repo.add_message(session_id=payload.session_id, role="student", content=payload.message)

    async def event_stream():
        yield "event: status\ndata: " + json.dumps({"phase": "retrieving_context"}) + "\n\n"
        try:
            response = await _service().chat(payload)
        except TutorProviderUnavailableError as exc:
            yield "event: error\ndata: " + json.dumps({"detail": str(exc)}) + "\n\n"
            return

        assistant_message = (
            response.assistant_message
            if hasattr(response, "assistant_message")
            else str(response.get("assistant_message", ""))
        )
        repo.add_message(session_id=payload.session_id, role="assistant", content=assistant_message)
        yield "event: status\ndata: " + json.dumps({"phase": "composing_response"}) + "\n\n"
        yield "event: message\ndata: " + json.dumps(response.model_dump()) + "\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/assessment/start", response_model=TutorAssessmentStartOut, status_code=status.HTTP_200_OK)
async def tutor_assessment_start(
    payload: TutorAssessmentStartIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )

    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")

    try:
        response = await _assessment_service(db).start_assessment(payload)
        LessonExperienceService.invalidate_session_cache(session_id=payload.session_id)
        return response
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/assessment/submit", response_model=TutorAssessmentSubmitOut, status_code=status.HTTP_200_OK)
async def tutor_assessment_submit(
    payload: TutorAssessmentSubmitIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="student_id must match authenticated user id",
        )

    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")

    try:
        response = await _assessment_service(db).submit_assessment(payload)
        LessonExperienceService.invalidate_session_cache(session_id=payload.session_id)
        return response
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/recap", response_model=TutorChatOut, status_code=status.HTTP_200_OK)
async def tutor_recap(
    payload: TutorRecapIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="student_id must match authenticated user id")
    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")
    try:
        return await _service().recap(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/drill", response_model=TutorChatOut, status_code=status.HTTP_200_OK)
async def tutor_drill(
    payload: TutorDrillIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="student_id must match authenticated user id")
    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")
    try:
        return await _service().drill(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/prereq-bridge", response_model=TutorChatOut, status_code=status.HTTP_200_OK)
async def tutor_prereq_bridge(
    payload: TutorPrereqBridgeIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="student_id must match authenticated user id")
    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")
    try:
        return await _service().prereq_bridge(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/study-plan", response_model=TutorChatOut, status_code=status.HTTP_200_OK)
async def tutor_study_plan(
    payload: TutorStudyPlanIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="student_id must match authenticated user id")
    repo = _session_repo(db)
    if not repo.session_exists_for_student(session_id=payload.session_id, student_id=payload.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found for this student.")
    try:
        return await _service().study_plan(payload)
    except TutorProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


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
