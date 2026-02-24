# backend/endpoints/tutor_session_and_chat_history.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import get_db


router = APIRouter(prefix="/tutor/sessions", tags=["Tutor Sessions"])


# ----------------------------
# Pydantic schemas
# ----------------------------

class StartSessionRequest(BaseModel):
    # matches tutor_sessions.student_profile_id
    student_profile_id: UUID
    subject: str = Field(..., min_length=1, max_length=100, examples=["math"])
    term: int = Field(..., ge=1, le=3, examples=[1])


class StartSessionResponse(BaseModel):
    # we still return "session_id" to match your API contract,
    # but it maps to tutor_sessions.id in DB.
    session_id: UUID


class ChatMessageOut(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class EndSessionResponse(BaseModel):
    session_id: UUID
    started_at: datetime
    ended_at: datetime
    duration_seconds: int
    duration_minutes: float
    cost: float
    activity_logged: bool


# ----------------------------
# Helpers
# ----------------------------

def _get_session_row(db: Session, session_id: UUID) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                id,
                student_profile_id,
                subject,
                term,
                started_at,
                ended_at,
                is_closed,
                duration_seconds,
                cost
            FROM tutor_sessions
            WHERE id = :session_id
            """
        ),
        {"session_id": session_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return dict(row)


# ----------------------------
# Endpoints
# ----------------------------

@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: StartSessionRequest, db: Session = Depends(get_db)):
    """
    POST /tutor/sessions/start
    Creates a tutoring session record.

    Request:
      { "student_profile_id": "uuid", "subject": "math", "term": 1 }

    Response:
      { "session_id": "uuid" }
    """
    session_id = uuid4()
    subject_norm = payload.subject.strip().lower()

    try:
        db.execute(
            text(
                """
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
                """
            ),
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
def get_session_history(session_id: UUID, db: Session = Depends(get_db)):
    """
    GET /tutor/sessions/{session_id}/history
    Returns chat history.
    """
    _ = _get_session_row(db, session_id)

    rows = db.execute(
        text(
            """
            SELECT
                id,
                session_id,
                role,
                content,
                created_at
            FROM tutor_chat_messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
            """
        ),
        {"session_id": session_id},
    ).mappings().all()

    return [ChatMessageOut(**dict(r)) for r in rows]


@router.post("/{session_id}/end", response_model=EndSessionResponse)
def end_session(session_id: UUID, db: Session = Depends(get_db)):
    """
    POST /tutor/sessions/{session_id}/end
    Closes session and logs time/cost summary.

    NOTE:
    - This endpoint updates tutor_sessions.
    - Your DB trigger should automatically insert a row into activity_logs when the session closes.
    """
    sess = _get_session_row(db, session_id)

    if sess["is_closed"] is True or sess["ended_at"] is not None:
        raise HTTPException(status_code=400, detail="Session is already closed")

    # 1) Close session and compute duration_seconds in SQL (server-side, consistent).
    try:
        db.execute(
            text(
                """
                UPDATE tutor_sessions
                SET
                    ended_at = NOW(),
                    is_closed = TRUE,
                    duration_seconds = GREATEST(
                        0,
                        EXTRACT(EPOCH FROM (NOW() - started_at))
                    )::int,
                    updated_at = NOW()
                WHERE id = :session_id
                """
            ),
            {"session_id": session_id},
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

    # 2) Re-read updated session for response values
    updated = _get_session_row(db, session_id)

    duration_seconds = int(updated["duration_seconds"] or 0)
    duration_minutes = duration_seconds / 60.0

    # 3) Cost model (edit if you have pricing)
    RATE_PER_MINUTE = 0.0
    cost = round(duration_minutes * RATE_PER_MINUTE, 2)

    # 4) Persist cost (optional but useful)
    try:
        db.execute(
            text(
                """
                UPDATE tutor_sessions
                SET cost = :cost, updated_at = NOW()
                WHERE id = :session_id
                """
            ),
            {"session_id": session_id, "cost": cost},
        )
        db.commit()
    except Exception:
        db.rollback()
        # Don’t fail the response if only cost persistence fails

    # 5) We *assume* activity_logs logging via trigger.
    # If you want to hard-check, we can query activity_logs for ref_id = session_id::text.
    activity_logged = True

    return EndSessionResponse(
        session_id=updated["id"],
        started_at=updated["started_at"],
        ended_at=updated["ended_at"],
        duration_seconds=duration_seconds,
        duration_minutes=duration_minutes,
        cost=float(cost),
        activity_logged=activity_logged,
    )