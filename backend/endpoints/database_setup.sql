-- ============================================================
-- 0) Extensions (needed for gen_random_uuid)
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1) Updated-at helper trigger (matches your schema style)
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 2) Tutor sessions table (aligned)
--    - references student_profiles(id)
--    - has created_at/updated_at
--    - duration_seconds + cost stored on end
-- ============================================================
CREATE TABLE IF NOT EXISTS tutor_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  student_profile_id uuid NOT NULL
    REFERENCES student_profiles(id)
    ON DELETE CASCADE,

  subject varchar NOT NULL,
  term int4 NOT NULL,

  started_at timestamptz NOT NULL DEFAULT NOW(),
  ended_at timestamptz,

  is_closed boolean NOT NULL DEFAULT FALSE,

  duration_seconds int4,
  cost numeric(12,2),

  created_at timestamptz NOT NULL DEFAULT NOW(),
  updated_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tutor_sessions_student_profile_id
  ON tutor_sessions(student_profile_id);

CREATE INDEX IF NOT EXISTS idx_tutor_sessions_started_at
  ON tutor_sessions(started_at);

DROP TRIGGER IF EXISTS trg_tutor_sessions_set_updated_at ON tutor_sessions;
CREATE TRIGGER trg_tutor_sessions_set_updated_at
BEFORE UPDATE ON tutor_sessions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- 3) Tutor chat messages table (aligned)
-- ============================================================
CREATE TABLE IF NOT EXISTS tutor_chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  session_id uuid NOT NULL
    REFERENCES tutor_sessions(id)
    ON DELETE CASCADE,

  role varchar NOT NULL,  -- 'student' | 'tutor' | 'system'
  content text NOT NULL,

  created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tutor_chat_messages_session_created
  ON tutor_chat_messages(session_id, created_at);

-- ============================================================
-- 4) activity_logs table (ONLY create if you don't already have it)
--    Your schema shows:
--      - id uuid
--      - student_id uuid
--      - subject varchar
--      - term int4
--      - event_type varchar
--      - ref_id varchar
--      - duration_seconds int4
--      - created_at timestamptz
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  student_id uuid NOT NULL,
  subject varchar NOT NULL,
  term int4 NOT NULL,

  event_type varchar NOT NULL,       -- e.g. 'tutor_session'
  ref_id varchar NOT NULL,           -- tutor_sessions.id stored as text

  duration_seconds int4,
  created_at timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_student_id_created
  ON activity_logs(student_id, created_at);

CREATE INDEX IF NOT EXISTS idx_activity_logs_event_type
  ON activity_logs(event_type);

-- ============================================================
-- 5) Auto-log to activity_logs when a session is ended
--    Trigger fires ONLY when session transitions into "closed"
--    and ended_at becomes NOT NULL.
--    It logs:
--      student_id  -> student_profiles.student_id
--      subject/term -> from tutor_sessions
--      ref_id      -> tutor_sessions.id::text
--      duration    -> tutor_sessions.duration_seconds
-- ============================================================
CREATE OR REPLACE FUNCTION log_tutor_session_to_activity_logs()
RETURNS trigger AS $$
DECLARE
  v_student_id uuid;
BEGIN
  -- Only run when transitioning from open -> closed
  IF (OLD.is_closed = FALSE AND NEW.is_closed = TRUE) AND NEW.ended_at IS NOT NULL THEN

    -- Get the "student_id" field from student_profiles
    SELECT sp.student_id
    INTO v_student_id
    FROM student_profiles sp
    WHERE sp.id = NEW.student_profile_id;

    -- If not found, block the update (data integrity)
    IF v_student_id IS NULL THEN
      RAISE EXCEPTION 'student_profiles.student_id not found for student_profile_id=%', NEW.student_profile_id;
    END IF;

    -- Insert activity log entry
    INSERT INTO activity_logs (
      id,
      student_id,
      subject,
      term,
      event_type,
      ref_id,
      duration_seconds,
      created_at
    ) VALUES (
      gen_random_uuid(),
      v_student_id,
      NEW.subject,
      NEW.term,
      'tutor_session',
      NEW.id::text,
      NEW.duration_seconds,
      NOW()
    );

  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_tutor_session_end ON tutor_sessions;
CREATE TRIGGER trg_log_tutor_session_end
AFTER UPDATE OF is_closed, ended_at, duration_seconds ON tutor_sessions
FOR EACH ROW
EXECUTE FUNCTION log_tutor_session_to_activity_logs();