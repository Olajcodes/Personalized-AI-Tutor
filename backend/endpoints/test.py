# /mnt/data/tutor_session_and_chat_history.py

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import get_db  # uses settings.database_url under the hood :contentReference[oaicite:2]{index=2}


router = APIRouter(prefix="/tutor/sessions", tags=["tutor-sessions"])


# -----------------------------
# Pydantic models
# -----------------------------

class StartSessionRequest(BaseModel):
    student_id: UUID
    subject: str = Field(..., min_length=1, max_length=64, examples=["math"])
    term: int = Field(..., ge=1, le=3, examples=[1])


class StartSessionResponse(BaseModel):
    session_id: UUID


class ChatMessageOut(BaseModel):
    message_id: UUID
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


# -----------------------------
# SQL helpers
# -----------------------------

def _ensure_session_exists(db: Session, session_id: UUID) -> dict:
    row = db.execute(
        text(
            """
            SELECT session_id, student_id, subject, term, started_at, ended_at, is_closed
            FROM tutor_sessions
            WHERE session_id = :session_id
            """
        ),
        {"session_id": session_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    return dict(row)


# -----------------------------
# Endpoints
# -----------------------------

@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: StartSessionRequest, db: Session = Depends(get_db)):
    """
    POST /tutor/sessions/start
    Creates a tutoring session record.
    Request:  { "student_id": "uuid", "subject": "math", "term": 1 }
    Response: { "session_id": "uuid" }
    """
    session_id = uuid4()

    try:
        db.execute(
            text(
                """
                INSERT INTO tutor_sessions (
                    session_id,
                    student_id,
                    subject,
                    term,
                    started_at,
                    ended_at,
                    is_closed
                )
                VALUES (
                    :session_id,
                    :student_id,
                    :subject,
                    :term,
                    NOW(),
                    NULL,
                    FALSE
                )
                """
            ),
            {
                "session_id": session_id,
                "student_id": payload.student_id,
                "subject": payload.subject.strip().lower(),
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
    _ = _ensure_session_exists(db, session_id)

    rows = db.execute(
        text(
            """
            SELECT
                message_id,
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
    """
    sess = _ensure_session_exists(db, session_id)

    if sess.get("is_closed") or sess.get("ended_at") is not None:
        raise HTTPException(status_code=400, detail="Session is already closed")

    # Update once, then compute summary from DB values to avoid timezone drift.
    try:
        db.execute(
            text(
                """
                UPDATE tutor_sessions
                SET ended_at = NOW(),
                    is_closed = TRUE
                WHERE session_id = :session_id
                """
            ),
            {"session_id": session_id},
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

    summary = db.execute(
        text(
            """
            SELECT
                session_id,
                started_at,
                ended_at,
                GREATEST(0, EXTRACT(EPOCH FROM (ended_at - started_at)))::bigint AS duration_seconds
            FROM tutor_sessions
            WHERE session_id = :session_id
            """
        ),
        {"session_id": session_id},
    ).mappings().first()

    if not summary:
        raise HTTPException(status_code=404, detail="Session not found after update")

    duration_seconds = int(summary["duration_seconds"])
    duration_minutes = duration_seconds / 60.0

    # Cost model (edit this):
    # - if you later store a rate per minute/hour, compute it here.
    RATE_PER_MINUTE = 0.0
    cost = float(round(duration_minutes * RATE_PER_MINUTE, 2))

    # Optional: persist the computed cost/duration in the session row
    try:
        db.execute(
            text(
                """
                UPDATE tutor_sessions
                SET duration_seconds = :duration_seconds,
                    cost = :cost
                WHERE session_id = :session_id
                """
            ),
            {"session_id": session_id, "duration_seconds": duration_seconds, "cost": cost},
        )
        db.commit()
    except Exception:
        # Don’t fail the request if persisting summary fails—return computed values anyway.
        db.rollback()

    return EndSessionResponse(
        session_id=summary["session_id"],
        started_at=summary["started_at"],
        ended_at=summary["ended_at"],
        duration_seconds=duration_seconds,
        duration_minutes=duration_minutes,
        cost=cost,
    )