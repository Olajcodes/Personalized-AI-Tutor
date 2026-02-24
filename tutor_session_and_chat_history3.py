from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import get_db

router = APIRouter(prefix="/tutor/sessions", tags=["tutor-sessions"])


# -------------------------------------------------------------------
# Pydantic models (aligned with database_setup.sql tables/column names)
# -------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    # tutor_sessions.student_profile_id (FK -> student_profiles.id)
    student_profile_id: UUID
    subject: str = Field(..., min_length=1, max_length=255, examples=["math"])
    term: int = Field(..., ge=1, le=3, examples=[1])


class StartSessionResponse(BaseModel):
    # API contract returns session_id, mapped to tutor_sessions.id
    session_id: UUID


class ChatMessageOut(BaseModel):
    # tutor_chat_messages columns
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class EndSessionResponse(BaseModel):
    # tutor_sessions columns + computed fields
    session_id: UUID
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    duration_minutes: float
    cost: float


# -----------------------------
# Internal helpers
# -----------------------------

def _ensure_student_profile_exists(db: Session, student_profile_id: UUID) -> None:
    row = db.execute(
        text("""
            SELECT id
            FROM student_profiles
            WHERE id = :id
        """),
        {"id": student_profile_id},
    ).first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid student_profile_id: {student_profile_id} does not exist in student_profiles",
        )


def _get_session(db: Session, session_id: UUID) -> dict:
    row = db.execute(
        text("""
            SELECT
                id,
                student_profile_id,
                subject,
                term,
                started_at,
                ended_at,
                is_closed,
                duration_seconds,
                cost,
                created_at,
                updated_at
            FROM tutor_sessions
            WHERE id = :id
        """),
        {"id": session_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return dict(row)


# -----------------------------
# Routes
# -----------------------------

@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: StartSessionRequest, db: Session = Depends(get_db)) -> StartSessionResponse:
    """
    POST /tutor/sessions/start
    Creates a tutoring session record.

    Database table used: tutor_sessions
      - id (uuid)
      - student_profile_id (uuid FK -> student_profiles.id)
      - subject (varchar)
      - term (int4)
      - started_at, ended_at (timestamptz)
      - is_closed (boolean)
      - duration_seconds (int4)
      - cost (numeric)
      - created_at, updated_at (timestamptz)
    """
    _ensure_student_profile_exists(db, payload.student_profile_id)

    session_id = uuid4()
    subject_norm = payload.subject.strip().lower()

    try:
        db.execute(
            text("""
                INSERT INTO tutor_sessions (
                    id,
                    student_profile_id,
                    subject,
                    term,
                    started_at,
                    ended_at,
                    is_closed,
                    duration_seconds,
                    cost,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :student_profile_id,
                    :subject,
                    :term,
                    NOW(),
                    NULL,
                    FALSE,
                    NULL,
                    NULL,
                    NOW(),
                    NOW()
                )
            """),
            {
                "id": session_id,
                "student_profile_id": payload.student_profile_id,
                "subject": subject_norm,
                "term": payload.term,
            },
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

    return StartSessionResponse(session_id=session_id)


@router.get("/{session_id}/history", response_model=List[ChatMessageOut])
def get_session_history(session_id: UUID, db: Session = Depends(get_db)) -> List[ChatMessageOut]:
    """
    GET /tutor/sessions/{session_id}/history
    Returns chat history for a session.

    Database table used: tutor_chat_messages
      - id (uuid)
      - session_id (uuid FK -> tutor_sessions.id)
      - role (varchar)
      - content (text)
      - created_at (timestamptz)
    """
    _ = _get_session(db, session_id)

    rows = db.execute(
        text("""
            SELECT
                id,
                session_id,
                role,
                content,
                created_at
            FROM tutor_chat_messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
        """),
        {"session_id": session_id},
    ).mappings().all()

    return [ChatMessageOut(**dict(r)) for r in rows]


@router.post("/{session_id}/end", response_model=EndSessionResponse)
def end_session(session_id: UUID, db: Session = Depends(get_db)) -> EndSessionResponse:
    """
    POST /tutor/sessions/{session_id}/end
    Closes session and logs time/cost summary.

    IMPORTANT:
    - Your database_setup.sql defines an AFTER UPDATE trigger on tutor_sessions.
      When is_closed becomes TRUE and ended_at is not NULL, it inserts a row into activity_logs.
      So this endpoint only needs to UPDATE tutor_sessions correctly.
    """
    sess = _get_session(db, session_id)

    if sess.get("is_closed") is True or sess.get("ended_at") is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already closed")

    # Cost model (keep simple; adjust as needed)
    RATE_PER_MINUTE = 0.0

    try:
        # Close the session and compute duration_seconds in SQL
        db.execute(
            text("""
                UPDATE tutor_sessions
                SET
                    ended_at = NOW(),
                    is_closed = TRUE,
                    duration_seconds = GREATEST(
                        0,
                        EXTRACT(EPOCH FROM (NOW() - started_at))
                    )::int,
                    updated_at = NOW()
                WHERE id = :id
            """),
            {"id": session_id},
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

    updated = _get_session(db, session_id)
    duration_seconds = int(updated.get("duration_seconds") or 0)
    duration_minutes = duration_seconds / 60.0
    cost = round(duration_minutes * RATE_PER_MINUTE, 2)

    # Persist cost (optional). This does NOT affect activity_logs trigger.
    try:
        db.execute(
            text("""
                UPDATE tutor_sessions
                SET cost = :cost, updated_at = NOW()
                WHERE id = :id
            """),
            {"id": session_id, "cost": cost},
        )
        db.commit()
    except Exception:
        db.rollback()
        # Don't fail the request if only cost update fails.

    # Re-fetch to ensure we return exact DB values (including cost if it saved)
    final_row = _get_session(db, session_id)

    return EndSessionResponse(
        session_id=final_row["id"],
        started_at=final_row["started_at"],
        ended_at=final_row["ended_at"],
        duration_seconds=int(final_row.get("duration_seconds") or duration_seconds),
        duration_minutes=float(duration_minutes),
        cost=float(final_row.get("cost") if final_row.get("cost") is not None else cost),
    )
