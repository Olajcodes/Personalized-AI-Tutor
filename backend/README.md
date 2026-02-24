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

## Run API

From repo root:

```bash
python -m uvicorn backend.main:app --reload
```

Swagger:
- `http://127.0.0.1:8000/docs`

## Mounted Routes (Current)

Base prefix: `/api/v1`

- `POST /auth/register`
- `POST /auth/login`
- `PUT /auth/password`
- `POST /students/profile/setup`
- `GET /students/profile`
- `PUT /students/profile`
- `PUT /students/users/{user_id}/preferences`
- `GET /metadata/subjects`
- `GET /learning/topics`
- `GET /learning/topics/{topic_id}/lesson`

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
  "role": "student"
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

`PUT /api/v1/students/users/{user_id}/preferences`

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
