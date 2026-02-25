"""Tutor session and chat history endpoints.

DB TRIGGER NOTE:
  The `log_tutor_session_to_activity_logs` trigger on `tutor_sessions` fires
  automatically on UPDATE and inserts into `activity_logs`. However it currently
  uses event_type='tutor_session' which violates the CHECK constraint.

  Fix it in Supabase SQL editor:

    CREATE OR REPLACE FUNCTION log_tutor_session_to_activity_logs()
    RETURNS TRIGGER AS $$
    DECLARE
      v_student_id UUID;
    BEGIN
      SELECT sp.student_id INTO v_student_id
      FROM student_profiles sp
      WHERE sp.id = NEW.student_profile_id;

      INSERT INTO activity_logs (
        id, student_id, subject, term, event_type, ref_id, duration_seconds, created_at
      ) VALUES (
        gen_random_uuid(),
        v_student_id,
        NEW.subject,
        NEW.term,
        'tutor_chat',   -- was 'tutor_session', which violates the CHECK constraint
        NEW.id::text,
        NEW.duration_seconds,
        NOW()
      );
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
"""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutor/sessions", tags=["Tutor Sessions"])

# activity_logs.event_type CHECK constraint allows ONLY:
# ['lesson_viewed', 'quiz_submitted', 'mastery_check_done', 'tutor_chat']
ALLOWED_TUTOR_EVENT_TYPE = "tutor_chat"

# ⚠️ Update this if your chat messages table has a different name.
# Run the query below in Supabase to find it:
#   SELECT table_name FROM information_schema.tables
#   WHERE table_schema = 'public'
#   AND (table_name ILIKE '%chat%' OR table_name ILIKE '%message%');
CHAT_MESSAGES_TABLE = "tutor_session_messages"


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
    student_profile_id: UUID,  # FK -> student_profiles.id, NOT the raw auth student_id
    subject: str,
    term: int,
    ref_id: str,
    duration_seconds: Optional[int] = None,
) -> None:
    """
    Logs to activity_logs table.

    IMPORTANT: activity_logs.student_id is a FK -> student_profiles.id,
    so we must pass student_profile_id here, not the auth/user student_id.

    event_type must be one of the allowed values in the DB CHECK constraint:
    ['lesson_viewed', 'quiz_submitted', 'mastery_check_done', 'tutor_chat']
    """
    db.execute(
        text(
            """
            INSERT INTO activity_logs (student_id, subject, term, event_type, ref_id, duration_seconds)
            VALUES (:student_id, :subject, :term, :event_type, :ref_id, :duration_seconds)
            """
        ),
        {
            "student_id": str(student_profile_id),  # FK to student_profiles.id
            "subject": subject,
            "term": term,
            "event_type": ALLOWED_TUTOR_EVENT_TYPE,
            "ref_id": ref_id,
            "duration_seconds": duration_seconds,
        },
    )


def _get_student_profile_id(db: Session, student_id: UUID) -> UUID:
    """
    tutor_sessions expects student_profile_id FK -> student_profiles.id.
    student_profiles has a student_id column pointing to the auth user.
    """
    row = db.execute(
        text(
            """
            SELECT id
            FROM student_profiles
            WHERE student_id = :student_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"student_id": str(student_id)},
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for student_id.",
        )
    return row[0]


def _get_session_context(db: Session, session_id: UUID) -> dict:
    """
    Returns session + student context by joining tutor_sessions -> student_profiles.
    Includes both student_profile_id (for activity_logs FK) and student_id (for reference).
    """
    row = db.execute(
        text(
            """
            SELECT
                ts.id            AS session_id,
                sp.id            AS student_profile_id,
                sp.student_id    AS student_id,
                ts.subject       AS subject,
                ts.term          AS term,
                ts.started_at    AS started_at,
                ts.ended_at      AS ended_at,
                ts.is_closed     AS is_closed
            FROM tutor_sessions ts
            JOIN student_profiles sp ON sp.id = ts.student_profile_id
            WHERE ts.id = :session_id
            LIMIT 1
            """
        ),
        {"session_id": str(session_id)},
    ).mappings().fetchone()
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

        session_id = db.execute(
            text(
                """
                INSERT INTO tutor_sessions (
                    student_profile_id, subject, term,
                    started_at, ended_at, is_closed, duration_seconds, cost
                )
                VALUES (
                    :student_profile_id, :subject, :term,
                    NOW(), NULL, FALSE, NULL, NULL
                )
                RETURNING id
                """
            ),
            {
                "student_profile_id": str(student_profile_id),
                "subject": subject,
                "term": payload.term,
            },
        ).scalar_one()

        # Log session_start — the trigger only fires on UPDATE (not INSERT),
        # so we log manually here.
        _log_activity(
            db,
            student_profile_id=student_profile_id,
            subject=subject,
            term=payload.term,
            ref_id=f"session_start:{session_id}",
            duration_seconds=None,
        )

        db.commit()
        logger.info("Started tutor session %s for student_profile %s", session_id, student_profile_id)
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
    Returns chat history ordered by created_at ascending.

    ⚠️ If this endpoint errors with UndefinedTable, update CHAT_MESSAGES_TABLE
    at the top of this file to match your actual table name. Find it with:
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND (table_name ILIKE '%chat%' OR table_name ILIKE '%message%');
    """
    ctx = _get_session_context(db, session_id)

    try:
        rows = db.execute(
            text(
                f"""
                SELECT id, session_id, role, content, created_at
                FROM tutor_chat_messages
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                """
            ),
            {"session_id": str(session_id)},
        ).mappings().all()

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
        logger.info("Fetched %d messages for session %s", len(messages), session_id)
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

    NOTE ON ACTIVITY LOGGING:
    The DB trigger `log_tutor_session_to_activity_logs` fires on UPDATE of
    tutor_sessions and handles inserting into activity_logs automatically.
    We do NOT call _log_activity here to avoid a duplicate entry.

    ⚠️ The trigger must use event_type='tutor_chat' to satisfy the CHECK constraint.
    See the trigger fix SQL at the top of this file.
    """
    ctx = _get_session_context(db, session_id)

    # If already closed, return stored values without re-updating
    if ctx.get("is_closed"):
        row = db.execute(
            text("SELECT duration_seconds, cost FROM tutor_sessions WHERE id = :session_id"),
            {"session_id": str(session_id)},
        ).mappings().fetchone()
        duration_seconds = int((row or {}).get("duration_seconds") or 0)
        cost = (row or {}).get("cost")
        return EndSessionResponse(session_id=session_id, duration_seconds=duration_seconds, cost=cost)

    try:
        row = db.execute(
            text(
                """
                UPDATE tutor_sessions
                SET
                    ended_at         = NOW(),
                    is_closed        = TRUE,
                    duration_seconds = GREATEST(
                        0,
                        FLOOR(EXTRACT(EPOCH FROM (NOW() - started_at)))
                    )::int,
                    updated_at       = NOW()
                WHERE id = :session_id
                RETURNING duration_seconds, cost
                """
            ),
            {"session_id": str(session_id)},
        ).mappings().fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Session not found.")

        duration_seconds = int(row["duration_seconds"] or 0)
        cost = row["cost"]

        # No manual _log_activity call here — the DB trigger handles it on UPDATE.
        # Once you apply the trigger fix above, it will log with event_type='tutor_chat'.

        db.commit()
        logger.info("Ended session %s — duration %ds", session_id, duration_seconds)
        return EndSessionResponse(session_id=session_id, duration_seconds=duration_seconds, cost=cost)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to end tutor session")
        raise HTTPException(status_code=500, detail=f"Failed to end session: {e}")
