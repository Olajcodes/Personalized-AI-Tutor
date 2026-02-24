# Mastery AI

Personalized AI Tutor with Knowledge Graph Memory for Adaptive Learning.

## Team

- Team Name: Team Mastery AI
- Program: Gen AI Fellowship Capstone Project

### Team Members

| Name | Area |
| --- | --- |
| Saheed Olayinka | AI Engineer, Backend (Lessons and Curriculum Delivery) |
| Lateef Abioye | AI Engineer, Backend (Activity, Streaks, Gamification) |
| Mary Adeoye | AI Engineer, Backend (Student Profile and Preferences) |
| Esther Kudoro | AI Engineer, Backend (Tutor Sessions and Chat History) |
| Adebimpe Atoyebi | AI Developer, Frontend (Login, Signup, Success) |
| Gbolahan | AI Developer, Frontend (Class, Subject, Learning Preference, Assessment Splash) |
| Favour | AI Developer, Frontend (Quiz and AI Progress Pages) |
| Olusola Somorin | AI Developer, Frontend (Student Mastery and Lesson Views) |
| Ajijolaoluwa Adesoji | AI Developer, Frontend (Mistake Explanation, Analytics Dashboards) |

## Problem Statement

Most classroom systems teach all learners at the same pace. This leaves prerequisite gaps unresolved and makes exam preparation inefficient. Standard LLM tutors improve accessibility but often remain short-memory chat systems without reliable concept tracking or prerequisite-aware planning.

## Solution Summary

Mastery AI is a curriculum-governed tutoring platform for SSS1 to SSS3 learners in Math, English, and Civic Education. It combines:

- persistent learner state,
- concept and prerequisite reasoning,
- adaptive tutoring and assessment loops,
- teacher-facing mastery visibility,
- admin governance for curriculum quality.

## Product Scope

- Target levels: `SSS1`, `SSS2`, `SSS3`
- Terms: `1`, `2`, `3`
- Subjects: `math`, `english`, `civic`
- User roles: `student`, `teacher`, `admin`

## Core Capabilities

- Curriculum-bound tutoring with level, term, and subject guardrails
- Concept-level mastery progression over time
- Diagnostic and quiz-driven adaptation
- Prerequisite-aware next-topic recommendations
- Teacher dashboards with class heatmaps and alerts
- Admin content ingestion, approval, and curriculum versioning

## Architecture

Mastery AI is split into two primary codebases in one repository:

1. `backend/` (FastAPI + PostgreSQL)
2. `ai-core/` (orchestration and AI logic)

### High-Level Flow

1. Frontend sends user action to backend API.
2. Backend resolves identity, scope, and persisted state.
3. For AI interactions, backend delegates to `ai-core` orchestration.
4. `ai-core` performs scope checks, retrieval, prerequisite lookup, generation, and lightweight mastery updates.
5. Backend persists outputs, history, and analytics-facing records.

### Data Components

- PostgreSQL: profiles, topics, lessons, activities, sessions, and relational state
- Neo4j: concept graph and prerequisite reasoning (integration layer in progress)
- Vector store: retrieval chunks and embeddings (integration layer in progress)
- Redis: optional caching layer for retrieval and orchestration

## Repository Structure

```text
Personalized-AI-Tutor/
|-- backend/
|   |-- alembic/
|   |-- core/
|   |-- endpoints/
|   |-- models/
|   |-- repositories/
|   |-- schemas/
|   |-- scripts/
|   |-- services/
|   |-- tests/
|   `-- main.py
|-- ai-core/
|   |-- core_engine/
|   |-- scripts/
|   `-- tests/
`-- README.md
```

## Tech Stack

- API: FastAPI
- ORM and migrations: SQLAlchemy, Alembic
- Relational DB: PostgreSQL
- Graph DB: Neo4j
- AI orchestration: LangGraph-compatible engine design (`ai-core`)
- Retrieval: vector-store abstraction in `ai-core`
- Security: JWT and password hashing utilities
- Testing: pytest

## Current Status

This repository is actively under development in team-parallel mode.

### Implemented and Working

- Curriculum metadata subjects endpoint
- Student-scoped topic listing
- Student-scoped lesson content delivery
- Migration and seed flow for curriculum lesson data
- Unit tests for lesson service logic

### Present but Not Fully Integrated Yet

- Auth endpoint module
- System health endpoint module
- AI-core provider and datastore integrations (partially stubbed)
- Full MVP endpoint surface from the normalized capstone API spec

## API Overview

Base URL: `/api/v1`

### Currently Mounted Routes

- `GET /metadata/subjects`
- `GET /learning/topics`
- `GET /learning/topics/{topic_id}/lesson`

### Examples of Planned MVP Routes

- `POST /tutor/chat`
- `POST /learning/diagnostic/start`
- `POST /learning/diagnostic/submit`
- `POST /learning/quizzes/generate`
- `POST /learning/quizzes/{quiz_id}/submit`
- `GET /learning/mastery`
- `GET /teachers/classes/{class_id}/heatmap`
- `POST /admin/curriculum/upload`

## Local Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- Git

Optional for extended integration:

- Neo4j
- Redis
- Vector DB provider

### 1) Clone

```bash
git clone https://github.com/Olajcodes/Personalized-AI-Tutor.git
cd Personalized-AI-Tutor
```

### 2) Backend Environment

Create `backend/.env` from `backend/.env.example` and set:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db>
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENV=dev
```

### 3) Install Dependencies

```bash
python -m pip install -r backend/requirements.txt pytest
python -m pip install -r ai-core/requirements.txt
```

### 4) Migrate and Seed Backend Data

Run from repository root:

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m backend.scripts.seed_lessons
```

### 5) Run Backend API

Run from repository root:

```bash
python -m uvicorn backend.main:app --reload
```

Swagger:

- `http://127.0.0.1:8000/docs`

## Endpoint Verification Guide (Current Working Scope)

Use these in Swagger or HTTP client after seed:

1. `GET /api/v1/metadata/subjects`
2. `GET /api/v1/learning/topics?student_id=00000000-0000-0000-0000-000000000001&subject=math&term=1`
3. Use returned `topic_id` in:
   - `GET /api/v1/learning/topics/{topic_id}/lesson?student_id=00000000-0000-0000-0000-000000000001`

Expected lesson response shape:

```json
{
  "topic_id": "uuid",
  "title": "Lesson title",
  "content_blocks": [
    { "type": "text", "value": "..." },
    { "type": "example", "value": { "...": "..." } },
    { "type": "exercise", "value": { "...": "..." } }
  ]
}
```

## AI Core Notes

Primary orchestration entrypoint:

- `core_engine.orchestration.tutor_engine.handle_question(...)`

The module structure already includes:

- curriculum policy checks,
- retrieval abstraction,
- prerequisite service abstraction,
- safety filtering,
- mastery update hook,
- cost and logging hooks.

Some integrations remain stubbed and are intended to be replaced as each team finalizes its owned service contracts.

## Testing

### Backend

```bash
python -m pytest -q backend/tests
```

### AI Core

```bash
python -m pytest -q ai-core/tests
```

## Contribution Workflow

1. Pull latest target branch.
2. Create a feature branch per task.
3. Keep PRs focused on one bounded scope.
4. Include migration notes if schema changes are introduced.
5. Include run and test instructions in PR description.
6. Attach sample request and response payloads for endpoint changes.

### Suggested Commit Format

- `feat: ...`
- `fix: ...`
- `chore: ...`
- `docs: ...`
- `test: ...`

## Security and Governance Notes

- Do not commit secrets, raw credentials, or private keys.
- Use `.env` files locally and secrets manager in deployment.
- Keep curriculum outputs grounded through retrieval and approval workflows.
- Keep learner data anonymized for demos and evaluation artifacts.

## Roadmap

- Complete full normalized MVP endpoint set
- Integrate AI-core orchestration with backend tutor routes
- Complete teacher analytics and intervention flows
- Complete admin ingestion and approval workflow
- Add CI checks for linting, tests, and schema consistency
- Prepare demo scripts and capstone presentation artifacts

## License

License selection is pending. Add an explicit `LICENSE` file before public release.
