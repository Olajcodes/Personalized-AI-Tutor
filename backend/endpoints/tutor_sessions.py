from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.repositories.tutor_session_repo import TutorSessionRepository
from backend.schemas.tutor_session_schema import (
    TutorSessionEndIn,
    TutorSessionEndOut,
    TutorSessionHistoryOut,
    TutorSessionStartIn,
    TutorSessionStartOut,
)
from backend.services.tutor_session_service import (
    TutorSessionNotFoundError,
    TutorSessionService,
)

router = APIRouter(prefix="/tutor/sessions", tags=["Tutor Sessions"])


def _service(db: Session) -> TutorSessionService:
    return TutorSessionService(TutorSessionRepository(db))


@router.post("/start", response_model=TutorSessionStartOut, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: TutorSessionStartIn,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/tutor/sessions/start
    Initializes a new AI Tutor session for a student using the StartIn schema.
    """
    try:
        return _service(db).start_session(payload=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


@router.get("/{session_id}/history", response_model=TutorSessionHistoryOut)
def get_session_history(
    session_id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """
    GET /api/v1/tutor/sessions/{session_id}/history
    Retrieves the full message history. Now requires student_id for validation 
    as per the service contract.
    """
    try:
        return _service(db).get_history(session_id=session_id, student_id=student_id)
    except TutorSessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{session_id}/end", response_model=TutorSessionEndOut)
def end_session(
    session_id: UUID,
    student_id: UUID,
    payload: TutorSessionEndIn,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/tutor/sessions/{session_id}/end
    Closes an active tutor session. Requires student_id to verify ownership 
    before marking the session as ended.
    """
    try:
        return _service(db).end_session(
            session_id=session_id,
            student_id=student_id,
            payload=payload
        )
    except TutorSessionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
