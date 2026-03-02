"""Internal Postgres contract endpoints.

These endpoints allow internal services (AI-core/graph/orchestration) to
retrieve profile/history data and persist internal attempt records.
They are not frontend-facing APIs.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.repositories.internal_postgres_repo import InternalPostgresRepository
from backend.schemas.internal_postgres_schema import (
    InternalClassRosterOut,
    InternalHistoryOut,
    InternalProfileOut,
    InternalQuizAttemptIn,
    InternalQuizAttemptOut,
)
from backend.services.internal_postgres_service import (
    InternalPostgresService,
    InternalProfileNotFoundError,
)

router = APIRouter(prefix="/internal/postgres", tags=["Internal Postgres Contracts"])


def _service(db: Session) -> InternalPostgresService:
    return InternalPostgresService(InternalPostgresRepository(db))


@router.get("/profile", response_model=InternalProfileOut)
def get_internal_profile(
    student_id: UUID,
    db: Session = Depends(get_db),
):
    """Return normalized profile context for internal services.

    Includes scope fields and learning preferences required by downstream agents.
    """
    try:
        return _service(db).get_profile(student_id=student_id)
    except InternalProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history", response_model=InternalHistoryOut)
def get_internal_history(
    student_id: UUID,
    session_id: UUID,
    db: Session = Depends(get_db),
):
    """Return session history for personalization and orchestration use cases.

    Requires both `student_id` and `session_id` for ownership validation.
    """
    return _service(db).get_history(student_id=student_id, session_id=session_id)


@router.post("/quiz-attempt", response_model=InternalQuizAttemptOut)
def create_internal_quiz_attempt(
    attempt_data: InternalQuizAttemptIn,
    db: Session = Depends(get_db),
):
    """Persist an internally generated quiz attempt record.

    Used when another service owns question generation but backend owns storage.
    """
    try:
        return _service(db).store_quiz_attempt(payload=attempt_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class-roster", response_model=InternalClassRosterOut)
def get_class_roster(
    class_id: UUID,
    db: Session = Depends(get_db),
):
    """Return student ids for a class roster.

    Used by internal analytics and bulk assignment workflows.
    """
    return _service(db).get_class_roster(class_id=class_id)
