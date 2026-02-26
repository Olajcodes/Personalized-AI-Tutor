from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

# IMPORTANT:
# - Keep this import consistent with your project structure.
# - If your get_db lives elsewhere, change this line accordingly.
from backend.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutor/sessions", tags=["Tutor Sessions"])

# activity_logs.event_type CHECK constraint allows ONLY:
# ['lesson_viewed', 'quiz_submitted', 'mastery_check_done', 'tutor_chat']
ALLOWED_TUTOR_EVENT_TYPE = "tutor_chat"


# -------------------------
# Pydantic Schemas
# -------------------------
class StartSessionRequest(BaseModel):
    student_id: UUID
    subject: str = Field(..., min_length=1, max_length=100)
    term: int = Field(..., ge=1)


class StartSessionResponse(BaseModel):
    session_id: UUID


class ChatMessage(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: str


class SessionHistoryResponse(BaseModel):
    session_id: UUID
    messages: List[ChatMessage]


class EndSessionResponse(BaseModel):
    session_id: UUID
    duration_seconds: int
    cost: Optional[float] = None


# -------------------------
# Helpers
# -------------------------
def _log_activity(
    db: Session,
    *,
    student_profile_id: UUID,  # FK -> student_profiles.id, NOT the raw student_id
    subject: str,
    term: int,
    ref_id: str,
    duration_seconds: Optional[int] = None,
) -> None:
    """
    Logs to activity_logs table.

    IMPORTANT: activity_logs.student_id is a FK -> student_profiles.id,
    so we must pass student_profile_id here, not the auth/user student_id.

    Because of the DB CHECK constraint on activity_logs.event_type,
    we MUST use event_type='tutor_chat' for tutor-related actions.

    We store the specific action context inside ref_id, e.g:
      - session_start:<session_id>
      - history_view:<session_id>
      - session_end:<session_id>
    """
    q = text(
        """
        INSERT INTO activity_logs (student_id, subject, term, event_type, ref_id, duration_seconds)
        VALUES (:student_id, :subject, :term, :event_type, :ref_id, :duration_seconds)
        """
    )
    db.execute(
        q,
        {
            "student_id": str(student_profile_id),  # ✅ FK to student_profiles.id
            "subject": subject,
            "term": term,
            "event_type": ALLOWED_TUTOR_EVENT_TYPE,  # ✅ must match DB constraint
            "ref_id": ref_id,
            "duration_seconds": duration_seconds,
        },
    )


def _get_student_profile_id(db: Session, student_id: UUID) -> UUID:
    """
    tutor_sessions expects student_profile_id FK -> student_profiles.id
    student_profiles has student_id column.
    """
    q = text(
        """
        SELECT id
        FROM student_profiles
        WHERE student_id = :student_id
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    row = db.execute(q, {"student_id": str(student_id)}).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for student_id.",
        )
    return row[0]


def _get_session_context(db: Session, session_id: UUID) -> dict:
    """
    Returns session + student context by joining tutor_sessions -> student_profiles.
    """
    q = text(
        """
        SELECT
            ts.id AS session_id,
            sp.id AS student_profile_id,
            sp.student_id AS student_id,
            ts.subject AS subject,
            ts.term AS term,
            ts.started_at AS started_at,
            ts.ended_at AS ended_at,
            ts.is_closed AS is_closed
        FROM tutor_sessions ts
        JOIN student_profiles sp ON sp.id = ts.student_profile_id
        WHERE ts.id = :session_id
        LIMIT 1
        """
    )
    row = db.execute(q, {"session_id": str(session_id)}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")
    return dict(row)


# -------------------------
# Endpoints
# -------------------------

@router.post("/start", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest, db: Session = Depends(get_db)):
    """
    POST /tutor/sessions/start
    Creates a tutoring session record.

    Request:  { "student_id": "uuid", "subject": "math", "term": 1 }
    Response: { "session_id": "uuid" }
    """
    try:
        student_profile_id = _get_student_profile_id(db, payload.student_id)
        subject = payload.subject.strip()

        insert_q = text(
            """
            INSERT INTO tutor_sessions (
                student_profile_id,
                subject,
                term,
                started_at,
                ended_at,
                is_closed,
                duration_seconds,
                cost
            )
            VALUES (
                :student_profile_id,
                :subject,
                :term,
                NOW(),
                NULL,
                FALSE,
                NULL,
                NULL
            )
            RETURNING id
            """
        )
        session_id = db.execute(
            insert_q,
            {
                "student_profile_id": str(student_profile_id),
                "subject": subject,
                "term": payload.term,
            },
        ).scalar_one()

        # ✅ Must use event_type='tutor_chat' due to DB check constraint
        # ✅ Pass student_profile_id (FK to student_profiles.id), not raw student_id
        _log_activity(
            db,
            student_profile_id=student_profile_id,
            subject=subject,
            term=payload.term,
            ref_id=f"session_start:{session_id}",
            duration_seconds=None,
        )

        db.commit()
        return StartSessionResponse(session_id=session_id)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to start tutor session")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {e}")


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
def get_session_history(session_id: UUID, db: Session = Depends(get_db)):
    """
    GET /tutor/sessions/{session_id}/history
    Returns chat history.

    NOTE:
    This assumes your chat messages table is named tutor_session_messages with columns:
      (id, session_id, role, content, created_at)

    If your actual table name/columns differ, update the SQL query below.
    """
    ctx = _get_session_context(db, session_id)

    try:
        msgs_q = text(
            """
            SELECT id, session_id, role, content, created_at
            FROM tutor_chat_messages
            WHERE session_id = :session_id
            ORDER BY created_at ASC
            """
        )
        rows = db.execute(msgs_q, {"session_id": str(session_id)}).mappings().all()

        messages = [
            ChatMessage(
                id=r["id"],
                session_id=r["session_id"],
                role=r["role"],
                content=r["content"],
                created_at=str(r["created_at"]),
            )
            for r in rows
        ]

        _log_activity(
            db,
            student_profile_id=UUID(str(ctx["student_profile_id"])),
            subject=str(ctx["subject"]),
            term=int(ctx["term"]),
            ref_id=f"history_view:{session_id}",
            duration_seconds=None,
        )

        db.commit()
        return SessionHistoryResponse(session_id=session_id, messages=messages)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to get session history")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {e}")


@router.post("/{session_id}/end", response_model=EndSessionResponse)
def end_session(session_id: UUID, db: Session = Depends(get_db)):
    """
    POST /tutor/sessions/{session_id}/end
    Closes session and logs time/cost summary.
    """
    ctx = _get_session_context(db, session_id)

    # If already closed, return stored values
    if ctx.get("is_closed"):
        q = text("SELECT duration_seconds, cost FROM tutor_sessions WHERE id = :session_id")
        row = db.execute(q, {"session_id": str(session_id)}).mappings().fetchone()
        duration_seconds = int((row or {}).get("duration_seconds") or 0)
        cost = (row or {}).get("cost")
        return EndSessionResponse(session_id=session_id, duration_seconds=duration_seconds, cost=cost)

    try:
        update_q = text(
            """
            UPDATE tutor_sessions
            SET
                ended_at = NOW(),
                is_closed = TRUE,
                duration_seconds = GREATEST(
                    0,
                    FLOOR(EXTRACT(EPOCH FROM (NOW() - started_at)))
                )::int,
                updated_at = NOW()
            WHERE id = :session_id
            RETURNING duration_seconds, cost
            """
        )
        row = db.execute(update_q, {"session_id": str(session_id)}).mappings().fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found.")

        duration_seconds = int(row["duration_seconds"] or 0)
        cost = row["cost"]

        # No _log_activity call here — the DB trigger log_tutor_session_to_activity_logs
        # fires automatically on UPDATE tutor_sessions and writes to activity_logs.
        # Calling _log_activity here too causes a duplicate/conflicting insert.

        db.commit()
        return EndSessionResponse(session_id=session_id, duration_seconds=duration_seconds, cost=cost)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to end tutor session")
        raise HTTPException(status_code=500, detail=f"Failed to end session: {e}")