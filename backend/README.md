# Mastery AI Backend

FastAPI backend for the Mastery AI capstone platform.

This document is the team runbook for local development and shared-database testing.

## What This Service Owns

- Auth and user management (register, login, password change)
- Student profile and learning preferences
- Curriculum metadata
- Student-scoped topics and lesson delivery
- PostgreSQL schema and migrations

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT (python-jose)

## Folder Layout

```text
backend/
|-- alembic/
|-- core/
|-- endpoints/
|-- models/
|-- repositories/
|-- schemas/
|-- scripts/
|-- services/
|-- tests/
`-- main.py
```

## Prerequisites

- Python installed and available on PATH
- Access to the shared PostgreSQL database
- `backend/.env` configured

## Environment Setup

Create `backend/.env`:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db>
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENV=dev
AI_CORE_BASE_URL=http://127.0.0.1:8100
AI_CORE_TIMEOUT_SECONDS=8
AI_CORE_ALLOW_FALLBACK=true
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:4173
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
USE_NEO4J_GRAPH=false
```

Notes:
- `backend/core/config.py` loads `backend/.env` directly.
- Run API commands from repo root to avoid import path issues.

## Install Dependencies

From repo root:

```bash
python -m pip install -r backend/requirements.txt pytest
```

## Migration Workflow (Shared DB)

### Apply latest migrations

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini current
```

Expected head includes:
- `0001_init`
- `0002_lesson_block_constraints`
- `0003_create_users_table`
- `0004_profile_user_fk`
- `0005_activity_tracking`
- `0006_learning_preferences`
- `0007_diagnostic_state`
- `0008_tutor_sessions_and_history`
- `0009_quiz_tables`
- `0010_graph_mastery_tracking`
- `0011_quiz_question_concept_id`
- `0012_student_stats_created_fix`
- `0013_activity_logs_timestamp_fix`
- `0014_tutor_sessions_reconcile`
- `0015_activity_event_check`
- `0016_activity_fk_reconcile`
- `0017_user_identity_fields`

### Important for shared DB

- Do not run downgrade on shared DB.
- Do not edit old migration files already used by teammates.
- Add a new migration file for any schema change.
- `alembic_version` is expected to be standalone (it is Alembic metadata, not a domain table).

## Seed Data Workflow

Seed script:

```bash
python -m backend.scripts.seed_lessons
```

Behavior:
- Idempotent for subjects/topics/lessons/blocks
- Creates or reuses default seed student profile
- Prints current topic IDs after each run

Default seed student:
- `00000000-0000-0000-0000-000000000001`

Current shared DB seed snapshot (from latest run):
- student_id: `00000000-0000-0000-0000-000000000001`
- math topic: `36718528-3a69-4365-88ab-757ce2b48e2c` (`Linear Equations`)
- english topic: `97abdcbd-bbf2-4d76-acc7-e9300f4786c1` (`Parts of Speech`)
- civic topic: `560e1ae5-2606-401a-a61b-2a74096c3acb` (`Citizen and the Constitution`)

Override if needed:

```bash
SEED_STUDENT_ID=<uuid> python -m backend.scripts.seed_lessons
```

PowerShell:

```powershell
$env:SEED_STUDENT_ID = "11111111-1111-1111-1111-111111111111"
python -m backend.scripts.seed_lessons
```

## Neo4j Graph Setup (Optional, Can Be Used Now)

You do not need to wait for a later section to seed graph data.

When enabled, internal graph endpoints (`/internal/graph/context` and `/internal/graph/update-mastery`) use Neo4j as primary storage and gracefully fall back to Postgres if Neo4j is unavailable.

### 1) Enable Neo4j in `backend/.env`

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
USE_NEO4J_GRAPH=true
```

### 2) Seed Topic/Concept Graph from Postgres Topics

```bash
python -m backend.scripts.seed_neo4j_graph
```

Optional demo student mastery edges:

PowerShell:

```powershell
$env:NEO4J_SEED_STUDENT_ID = "00000000-0000-0000-0000-000000000001"
python -m backend.scripts.seed_neo4j_graph
```

### 3) Verify Quickly

- `GET /api/v1/internal/graph/context?student_id=<uuid>&subject=math&sss_level=SSS1&term=1`
- `POST /api/v1/internal/graph/update-mastery` with valid payload

If Neo4j is reachable and enabled, updates are mirrored there; if not, requests still work via Postgres fallback.

## Run API

From repo root:

```bash
python -m uvicorn backend.main:app --reload
```

Swagger:
- `http://127.0.0.1:8000/docs`

## Docker Runtime

From repo root:

```bash
docker compose up --build
```

Backend container:
- runs `alembic upgrade head` at startup
- serves API on `http://127.0.0.1:8000`

## Mounted Routes (Current)

Base prefix: `/api/v1`

- `POST /auth/register`
- `POST /auth/login`
- `PUT /auth/password`
- `POST /students/profile/setup`
- `GET /students/profile`
- `PUT /students/profile`
- `PUT /students/users/{user_id}/preferences`
- `GET /users/me`
- `PUT /users/me`
- `PUT /users/{user_id}/preferences`
- `GET /metadata/subjects`
- `GET /metadata/levels`
- `GET /learning/topics`
- `GET /learning/topics/{topic_id}/lesson`
- `POST /learning/activity/log`
- `GET /students/stats`
- `GET /students/leaderboard`
- `GET /system/health`
- `POST /tutor/sessions/start`
- `GET /tutor/sessions/{session_id}/history`
- `POST /tutor/sessions/{session_id}/end`
- `POST /tutor/chat`
- `POST /tutor/hint`
- `POST /tutor/explain-mistake`
- `GET /internal/postgres/profile`
- `GET /internal/postgres/history`
- `POST /internal/postgres/quiz-attempt`
- `GET /internal/postgres/class-roster`
- `POST /learning/diagnostic/start`
- `POST /learning/diagnostic/submit`
- `POST /learning/path/next`
- `GET /learning/path/map/visual`
- `GET /internal/graph/context`
- `POST /internal/graph/update-mastery`
- `POST /learning/quizzes/generate`
- `POST /learning/quizzes/{quiz_id}/submit`
- `GET /learning/quizzes/{quiz_id}/results`
- `GET /learning/mastery`

## Shared DB Test Runbook (Team Standard)

Use this exact sequence for reliable testing on the shared database.

### 1) Auth: create isolated test user

In Swagger:
- `POST /api/v1/auth/register`

Sample payload (use unique email every time):

```json
{
  "email": "yourname+test001@example.com",
  "password": "password123",
  "role": "student",
  "first_name": "Olasquare",
  "last_name": "Adeola"
}
```

Why:
- Shared DB means duplicate email causes `409`.
- Include timestamp/random suffix in email to avoid collisions.

### 2) Login and authorize

- `POST /api/v1/auth/login`

```json
{
  "email": "yourname+test001@example.com",
  "password": "password123"
}
```

Expected login response now includes `user_id`:

```json
{
  "access_token": "<jwt>",
  "user_id": "<uuid>",
  "role": "student",
  "first_name": "Olasquare",
  "last_name": "Adeola",
  "display_name": "Olasquare Adeola"
}
```

JWT payload includes both `user_id` and `student_id` claims (same UUID).

- Copy `access_token`
- Click `Authorize` in Swagger and provide:
  - `Bearer <access_token>`

### 3) Profile setup (first-time user)

Use `user_id` from register response as `student_id`.

- `POST /api/v1/students/profile/setup`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "sss_level": "SSS1",
  "subjects": ["math", "english", "civic"],
  "term": 1
}
```

Important:
- If you set a different `student_id` than your auth user ID, `GET /students/profile` will likely return not found.

### 3a) User profile identity (dashboard card)

- `GET /api/v1/users/me`

Expected fields:
- `first_name`
- `last_name`
- `display_name`
- `avatar_url`
- `phone`

- `PUT /api/v1/users/me`

Sample payload:

```json
{
  "display_name": "Olasquare A.",
  "phone": "+2348012345678",
  "avatar_url": "https://cdn.example.com/avatar/olasquare.png"
}
```

### 4) Verify profile

- `GET /api/v1/students/profile`

Expected:
- profile object for authenticated user
- subject list present

### 5) Verify metadata + curriculum delivery

- `GET /api/v1/metadata/subjects`
- `GET /api/v1/learning/topics?student_id=<student_id>&subject=math&term=1`
- `GET /api/v1/learning/topics/{topic_id}/lesson?student_id=<student_id>`

Use `topic_id` from the topics endpoint response (do not hardcode across team runs).

Known valid sample query from current seed:
- `GET /api/v1/learning/topics?student_id=00000000-0000-0000-0000-000000000001&subject=math&term=1`
- `GET /api/v1/learning/topics/36718528-3a69-4365-88ab-757ce2b48e2c/lesson?student_id=00000000-0000-0000-0000-000000000001`

### 6) Password change validation

- `PUT /api/v1/auth/password`

```json
{
  "current_password": "password123",
  "new_password": "newpassword123"
}
```

Then login again with `newpassword123`.

### 7) Activity + stats quick validation

- `POST /api/v1/learning/activity/log`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "subject": "math",
  "term": 1,
  "event_type": "lesson_viewed",
  "ref_id": "topic-linear-equations",
  "duration_seconds": 120
}
```

- `GET /api/v1/students/stats`
- `GET /api/v1/students/leaderboard`

Expected:
- `stats` reflects non-zero study time and points after log call.
- `leaderboard` contains ranked entries.
- `student_id` in log request must match authenticated token user id.

### 8) Section 2 smoke test (Sessions + Internal Postgres)

Status:
- Completed.

Session start:
- `POST /api/v1/tutor/sessions/start`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "subject": "math",
  "term": 1
}
```

Expected:
- returns `session_id`

Session history:
- `GET /api/v1/tutor/sessions/{session_id}/history?student_id=<student_uuid>`

Expected:
- returns ordered `messages` array for that session

Session end:
- `POST /api/v1/tutor/sessions/{session_id}/end?student_id=<student_uuid>`

```json
{
  "total_tokens": 350,
  "prompt_tokens": 200,
  "completion_tokens": 150,
  "cost_usd": 0.01,
  "end_reason": "user_exit"
}
```

Expected:
- session marked ended with `duration_seconds` and cost summary

Internal Postgres profile:
- `GET /api/v1/internal/postgres/profile?student_id=<student_uuid>`

Expected:
- `student_id`, `sss_level`, `term`, `subjects`, `preferences`

Internal Postgres history:
- `GET /api/v1/internal/postgres/history?student_id=<student_uuid>&session_id=<session_uuid>`

Expected:
- session-bound `messages` list

Internal quiz attempt:
- `POST /api/v1/internal/postgres/quiz-attempt`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "quiz_id": "11111111-1111-1111-1111-111111111111",
  "subject": "math",
  "sss_level": "SSS1",
  "term": 1,
  "answers": [{ "question_id": "q1", "answer": "B" }],
  "time_taken_seconds": 120,
  "score": 80
}
```

Expected:
- `attempt_id`, `stored=true`, `created_at`

Internal class roster:
- `GET /api/v1/internal/postgres/class-roster?class_id=<class_uuid>`

Expected:
- `class_id` and `student_ids` list (empty list allowed before teacher section)

### 9) Section 3 smoke test (Diagnostic + Path + Internal Graph)

Status:
- Completed.
- Backed by persisted diagnostic state and graph mastery tracking tables.

Diagnostic start:
- `POST /api/v1/learning/diagnostic/start`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "subject": "english",
  "sss_level": "SSS1",
  "term": 1
}
```

Expected:
- `diagnostic_id`
- `concept_targets`
- `questions`

Diagnostic submit:
- `POST /api/v1/learning/diagnostic/submit`

```json
{
  "diagnostic_id": "PUT_DIAGNOSTIC_ID_HERE",
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "answers": [
    { "question_id": "PUT_QUESTION_ID_FROM_START_RESPONSE", "answer": "A" }
  ]
}
```

Expected:
- `baseline_mastery_updates`
- `recommended_start_topic_id`

Path next:
- `POST /api/v1/learning/path/next`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "subject": "math",
  "sss_level": "SSS2",
  "term": 2
}
```

Expected:
- `recommended_topic_id`
- `reason`
- `prereq_gaps`

Learning map visual:
- `GET /api/v1/learning/path/map/visual?student_id=<student_uuid>&subject=math&sss_level=SSS1&term=1&view=topic`

Expected:
- list of nodes with `mastered`/`current`/`locked` status for scoped topics

Internal graph context:
- `GET /api/v1/internal/graph/context?student_id=<student_uuid>&subject=math&sss_level=SSS1&term=1`

Expected:
- scoped graph context payload with mastery, prerequisite edges, unlocked nodes, and overall mastery

Internal graph update:
- `POST /api/v1/internal/graph/update-mastery`

```json
{
  "student_id": "PUT_REGISTER_USER_ID_HERE",
  "quiz_id": "11111111-1111-1111-1111-111111111111",
  "attempt_id": "22222222-2222-2222-2222-222222222222",
  "subject": "math",
  "sss_level": "SSS2",
  "term": 2,
  "timestamp": "2026-02-23T10:00:00Z",
  "source": "practice",
  "concept_breakdown": [
    { "concept_id": "concept-a", "is_correct": true, "weight_change": 0.15 },
    { "concept_id": "concept-b", "is_correct": false, "weight_change": -0.05 }
  ]
}
```

Expected:
- success acknowledgement from graph adapter/client service

## Quick Test Payloads

### Register

```json
{
  "email": "qa+<timestamp>@example.com",
  "password": "password123",
  "role": "student"
}
```

### Login

```json
{
  "email": "qa+<timestamp>@example.com",
  "password": "password123"
}
```

### Setup Profile

```json
{
  "student_id": "<register.user_id>",
  "sss_level": "SSS1",
  "subjects": ["math", "english"],
  "term": 1
}
```

### Update Preferences

Use either path:
- `PUT /api/v1/students/users/{user_id}/preferences` (backward compatible)
- `PUT /api/v1/users/{user_id}/preferences` (normalized contract)

```json
{
  "explanation_depth": "standard",
  "examples_first": true,
  "pace": "normal"
}
```

## Automated Test Commands

Run all backend tests:

```bash
python -m pytest -q backend/tests
```

Run only auth tests:

```bash
python -m pytest -q backend/tests/unit/test_auth_service.py
```

## Common Issues

### 1) `ModuleNotFoundError: No module named 'backend'`

Cause:
- Running uvicorn from `backend/` with wrong module path.

Fix:
- Run from repo root:
  - `python -m uvicorn backend.main:app --reload`

### 2) `409` on register

Cause:
- Email already exists in shared DB.

Fix:
- Use unique email.

### 3) `404 Student profile not found` after login

Cause:
- Profile not set up for authenticated user ID.

Fix:
- Run `POST /students/profile/setup` using your register `user_id` as `student_id`.

### 4) Topic/lesson IDs change

Cause:
- Shared DB updates by other team members.

Fix:
- Fetch current `topic_id` via `/learning/topics` first.

## Team Rules for Shared DB

- Always use unique emails for auth testing.
- Never delete or mutate another teammate's test rows manually.
- Use additive migrations only.
- Announce schema changes before merging.
- Attach request/response examples in your PR for endpoint changes.

## Required Team Documentation Update

Every team must add their own testing block to this `backend/README.md` for cross-team validation.

Minimum required content per team:
- endpoint list they own
- exact request payload examples
- exact response examples
- any required seeded rows, IDs, or tokens
- known constraints (for example role checks, required order of calls)
- one quick smoke-test sequence that another teammate can run in under 5 minutes

Suggested section format:

```md
## Team: <team name>
- Owned endpoints:
  - ...
- Sample data:
  - ...
- Smoke test:
  1) ...
  2) ...
```








### Section 4 - Quiz Lifecycle (Generate, Submit, Results)

Smoke test steps:
1. Ensure database is migrated: `python -m alembic -c backend/alembic.ini upgrade head`
2. Start the backend server from repo root: `python -m uvicorn backend.main:app --reload`
3. (Optional) start ai-core service if remote generation is enabled: `python -m uvicorn ai_core.main:app --port 8001 --reload`
4. Generate quiz: `POST /api/v1/learning/quizzes/generate`
5. Submit answers: `POST /api/v1/learning/quizzes/{quiz_id}/submit`
6. Fetch results: `GET /api/v1/learning/quizzes/{quiz_id}/results?student_id=...&attempt_id=...`
7. Run backend section-4 unit tests: `python -m pytest -q backend/tests/unit/test_quiz_generate_service.py backend/tests/unit/test_quiz_submit_service.py backend/tests/unit/test_quiz_results_service.py backend/tests/unit/test_quiz_endpoints.py`
8. Run ai-core quiz tests: `python -m pytest -q ai_core/tests/unit/test_quiz_engine.py`
9. Integration note: set `TEST_DATABASE_URL=postgresql://...` and run `python -m pytest -q backend/tests/integration/test_section4_quiz_flow.py` for real section-4 E2E.

### Section 5 - Tutor AI + Mastery Dashboard MVP

Smoke test steps:
1. Ensure database is migrated: `python -m alembic -c backend/alembic.ini upgrade head`
2. Start backend: `python -m uvicorn backend.main:app --reload`
3. Start ai-core (optional; fallback works if unavailable): `python -m uvicorn ai_core.main:app --port 8001 --reload`
4. Create/start a tutor session:
   - `POST /api/v1/tutor/sessions/start`
   - Save returned `session_id`.
5. Send tutor chat:
   - `POST /api/v1/tutor/chat`
   - Sample body:
   ```json
   {
     "student_id": "PUT_USER_ID_HERE",
     "session_id": "PUT_SESSION_ID_HERE",
     "subject": "math",
     "sss_level": "SSS2",
     "term": 1,
     "topic_id": "PUT_TOPIC_ID_HERE",
     "message": "Explain linear equations with one example."
   }
   ```
6. Request a hint:
   - `POST /api/v1/tutor/hint`
7. Request explain-mistake:
   - `POST /api/v1/tutor/explain-mistake`
8. Fetch mastery dashboard:
   - `GET /api/v1/learning/mastery?student_id=...&subject=math&term=1&view=concept`
9. Run section-5 unit tests:
   - `python -m pytest -q backend/tests/unit/test_tutor_orchestration_service.py backend/tests/unit/test_mastery_dashboard_service.py backend/tests/unit/test_tutor_endpoints.py backend/tests/unit/test_mastery_endpoints.py`
10. Run ai-core tutor tests:
    - `python -m pytest -q ai_core/tests/unit/test_tutor_engine.py`
11. Integration note:
    - set `TEST_DATABASE_URL=postgresql://...`
    - run `python -m pytest -q backend/tests/integration/test_section5_tutor_mastery_flow.py`

### Section 7 - Admin Curriculum + Governance + Internal RAG

Smoke test steps (run in order):
1. Install new dependencies:
   - `python -m pip install -r backend/requirements.txt`
2. Apply migrations:
   - `python -m alembic -c backend/alembic.ini upgrade head`
3. Ensure env is configured for vector retrieval:
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - `QDRANT_COLLECTION`
   - `QDRANT_EMBEDDING_MODEL`
4. Start backend:
   - `python -m uvicorn backend.main:app --reload`
5. Login as an `admin` user and authorize token in Swagger.
6. Upload curriculum scope:
   - `POST /api/v1/admin/curriculum/upload`
   - sample payload:
   ```json
   {
     "subject": "math",
     "sss_level": "SSS1",
     "term": 1,
     "source_root": "C:/Users/OLASQUARE/Desktop/GEN AI Works/Personalized-AI-Tutor/docs/SSS_NOTES_2026",
     "version_name": "math-sss1-term1-2026-v1"
   }
   ```
7. Track ingestion:
   - `GET /api/v1/admin/curriculum/ingestion-status`
   - optional filter: `GET /api/v1/admin/curriculum/ingestion-status?job_id=<job_id>`
8. Check approval queue:
   - `GET /api/v1/admin/curriculum/pending-approvals`
9. Publish a version:
   - `POST /api/v1/admin/curriculum/versions/{version_id}/approve`
10. Retrieve internal RAG chunks:
    - `POST /api/v1/internal/rag/retrieve`
    - sample payload:
    ```json
    {
      "query": "Explain linear equation with one solved example",
      "subject": "math",
      "sss_level": "SSS1",
      "term": 1,
      "topic_ids": [],
      "top_k": 6,
      "approved_only": true
    }
    ```
11. Governance metrics and review:
    - `GET /api/v1/admin/governance/metrics`
    - `GET /api/v1/admin/governance/hallucinations?status=open&limit=20`
    - `POST /api/v1/admin/governance/hallucinations/{id}/resolve`
12. Run section-7 tests:
    - `python -m pytest -q backend/tests/unit/test_admin_curriculum_service.py backend/tests/unit/test_governance_service.py backend/tests/unit/test_internal_rag_endpoint.py backend/tests/unit/test_system_health_endpoint.py backend/tests/integration/test_section7_admin_flow.py`
