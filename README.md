# Mastery AI

Mastery AI is a curriculum-governed personalized learning platform for senior secondary students.
It combines a FastAPI backend, an AI-core orchestration service, a vector store, and a concept graph
to deliver topic recommendations, tutoring, quizzes, and mastery tracking.

## Team

- Team Name: Team Mastery AI
- Program: Gen AI Fellowship Capstone Project

## Architecture

- `frontend/`: React web application
- `backend/`: FastAPI API, auth, profile, curriculum governance, persistence
- `ai_core/`: AI orchestration (tutor, quiz generation/insights, safety, retrieval helpers)
- `PostgreSQL`: transactional data
- `Qdrant`: curriculum chunk vectors
- `Neo4j`: topic/concept prerequisite graph

## Repository Layout

```text
Personalized-AI-Tutor/
|-- frontend/
|-- backend/
|   |-- alembic/
|   |-- core/
|   |-- endpoints/
|   |-- models/
|   |-- repositories/
|   |-- schemas/
|   |-- scripts/
|   |-- services/
|   `-- main.py
|-- ai_core/
|   |-- core_engine/
|   `-- main.py
`-- docs/
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop

## Fresh Start (Verified Local Setup)

Run every command from repository root unless stated otherwise.
Recommended local mode:

- Docker for infrastructure only: PostgreSQL, Redis, Neo4j, Qdrant
- Backend, AI Core, and Frontend run on the host machine

Verified local ports:

- Frontend: `5173` or `5174`
- Backend: `8001`
- AI Core: `10001`
- Postgres: `55432`
- Redis: `6379`
- Neo4j HTTP: `7474`
- Neo4j Bolt: `7687`
- Qdrant: `6333`

### 1) Clone

```bash
git clone https://github.com/Olajcodes/Personalized-AI-Tutor.git
cd Personalized-AI-Tutor
```

### 2) Python environment and dependencies

```bash
python -m venv .venv
```

Activate:

- PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

- bash/zsh:
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip install -r ai_core/requirements.txt
```

### 3) Frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4) Environment files

Create env files from examples:

- PowerShell:
```powershell
copy backend\.env.example backend\.env
copy ai_core\.env.example ai_core\.env
copy frontend\.env.example frontend\.env
```

- bash/zsh:
```bash
cp backend/.env.example backend/.env
cp ai_core/.env.example ai_core/.env
cp frontend/.env.example frontend/.env
```

Set required secrets/URLs, especially:

- `backend/.env`
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `AI_CORE_BASE_URL` (local default: `http://127.0.0.1:10001`)
  - `CORS_ORIGINS` (include local frontend + production frontend domain)
  - `INTERNAL_SERVICE_KEY` (must match ai-core)
- `ai_core/.env`
  - `GROQ_API_KEY` or `LLM_API_KEY`
  - `INTERNAL_SERVICE_KEY` (must match backend)
  - `POSTGRES_DSN`
  - `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `frontend/.env`
  - `VITE_API_URL=http://127.0.0.1:8001/api/v1`
  - `VITE_AI_CORE_URL=http://127.0.0.1:10001`
  - any auth-related frontend variables already used by your UI

Important:

- `backend/.env` and `ai_core/.env` must use the same `INTERNAL_SERVICE_KEY`
- for the verified Docker-backed local DB, use:
  - `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:55432/mastery_ai`
  - `POSTGRES_DSN=postgresql://postgres:postgres@127.0.0.1:55432/mastery_ai`
- if Vite starts on `5174`, make sure `CORS_ORIGINS` includes both `5173` and `5174`

### 5) Start local infrastructure with Docker

Recommended local flow:

- run infrastructure in Docker
- run backend, ai-core, and frontend on the host machine

Start infra:

```powershell
docker compose up -d postgres redis neo4j qdrant
```

Confirm containers are healthy:

```powershell
docker compose ps
```

Services exposed locally:

- Postgres: `127.0.0.1:55432`
- Redis: `127.0.0.1:6379`
- Neo4j HTTP: `127.0.0.1:7474`
- Neo4j Bolt: `127.0.0.1:7687`
- Qdrant: `127.0.0.1:6333`

Optional: run the full stack in Docker instead of host-run backend/ai-core:

```powershell
docker compose --profile fullstack up --build
```

### 6) Apply database migrations

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

Optional but recommended:

```bash
python -m alembic -c backend/alembic.ini current
```

### 7) Validate and seed curriculum

Validate the canonical JSON tree first:

```powershell
python -m backend.scripts.validate_curriculum_json --source-root docs/Curriculum_in_json
```

Then run the full local reset/reseed:

This is the recommended clean baseline command. It reseeds baseline curriculum entities, ingests all detected scopes from `docs/Curriculum_in_json`, auto-approves versions, and reseeds Neo4j.

```powershell
python -m backend.scripts.reset_and_reseed_curriculum `
  --source-root "docs/Curriculum_in_json" `
  --seed-reset `
  --no-seed-demo-learners `
  --no-disable-neo4j-sync `
  --seed-neo4j `
  --qdrant-batch-size 24 `
  --qdrant-timeout-seconds 240 `
  --full-db-reset
```

Notes:

- LLM extraction/inference is enabled by default in this flow.
- The verified corpus for local setup is `docs/Curriculum_in_json`.
- If LLM is unavailable or output is invalid, ingestion falls back safely and logs fallback mode.
- Use `--disable-llm` only for deterministic fallback-only runs.
- Add `--full-db-reset` if you want to truncate all public application tables before reseeding.
- If you include demo learners, the seed flow now creates identity/profile scope only. It does not fabricate concept mastery.

### 8) Run services

Use three terminals after the seed finishes.

Terminal 1: Backend

```bash
python -m uvicorn backend.main:app --reload --port 8001
```

Terminal 2: AI Core

```bash
python -m uvicorn ai_core.main:app --reload --port 10001
```

Terminal 3: Frontend

```bash
cd frontend
npm run dev
```

Recommended local URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://127.0.0.1:8001`
- AI Core: `http://127.0.0.1:10001`

If Vite starts on `5174`, use `http://localhost:5174`.

## Health Checks

- Backend Swagger: `http://127.0.0.1:8001/docs`
- Backend health: `http://127.0.0.1:8001/api/v1/system/health`
- AI Core health: `http://127.0.0.1:10001/health`
- Neo4j browser: `http://127.0.0.1:7474`

Neo4j local browser credentials, if you keep the default local Docker auth:

- username: `neo4j`
- password: `olayiwola`

If Vite moves to `5174`, add that origin to `backend/.env` `CORS_ORIGINS` and restart the backend.

## First Run Checklist

After the app is up:

1. Open the frontend
2. Register or log in
3. Complete onboarding
4. Finish the diagnostic for all selected subjects
5. Open dashboard
6. Open a course
7. Open a lesson
8. Open AI Tutor
9. Run a quiz

If the lesson pages load but graph data or tutoring feels empty, the most common cause is that the curriculum reset/reseed step was skipped or failed partway through.

## Common Local Issues

- `The server is taking too long`
  - backend is not running, or is blocked during startup
  - check backend terminal and `http://127.0.0.1:8001/api/v1/system/health`
- `Origin is not allowed` for Google auth
  - your Google client does not allow the local frontend origin
  - either add `http://localhost:5173` / `5174` to Google OAuth origins or disable Google locally
- `No topics available`
  - confirm the reseed completed successfully
  - confirm migrations are applied
  - confirm curriculum JSON validation passed
- Neo4j graph looks empty
  - confirm Docker Neo4j is running
  - confirm `USE_NEO4J_GRAPH=true`
  - confirm the reset/reseed command included `--seed-neo4j`

Health payloads now expose runtime visibility, not only dependency checks:

- Backend `/api/v1/system/health`
  - `checks.prewarm_queue`
  - `runtime.telemetry`
  - `runtime.caches`
- AI Core `/health`
  - `runtime.telemetry`

## Demo Runtime Dock

Student routes now include a collapsible runtime dock for presentation/debug use.

- Open the dock with the floating `Live runtime` button
- Keyboard shortcut: `Shift + D`
- The dock shows:
  - latest graph intervention summary
  - backend prewarm queue state
  - lesson/course/dashboard cache counts
  - hottest backend and ai-core graph-first paths

If ai-core runtime is not visible in the dock, set:

```env
VITE_AI_CORE_URL=http://127.0.0.1:10001
```

You can also override it temporarily in the browser:

```js
localStorage.setItem('mastery_ai_core_url', 'http://127.0.0.1:10001')
```

## Production Notes

- Keep `AI_CORE_ALLOW_FALLBACK=false` in strict production environments if you want hard failure when AI Core is unreachable.
- Configure `CORS_ORIGINS` explicitly; avoid `*` in production.
- Keep secrets only in secret managers (Render/CI/CD), not in git-tracked files.
- Keep the same `INTERNAL_SERVICE_KEY` on backend and ai-core so internal adapters stay locked down.
- Keep curriculum ingestion and approval as an admin-only workflow.
- Backend runs an in-process prewarm worker by default. Keep `PREWARM_QUEUE_ENABLED=true` unless you are deliberately debugging cache behavior.

## Deployment

The repository includes `render.yaml` for Render Blueprint deployment.

At minimum configure:

- Backend:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `AI_CORE_BASE_URL`
  - `CORS_ORIGINS`
  - `INTERNAL_SERVICE_KEY`
- AI Core:
  - `GROQ_API_KEY` or `LLM_API_KEY`
  - `INTERNAL_SERVICE_KEY`
  - datastore credentials (`POSTGRES_DSN`, `QDRANT_*`, `NEO4J_*`)

## Service-Specific Documentation

- Backend operations and API details: [backend/README.md](./backend/README.md)
- AI-core runtime and endpoints: [ai_core/README.md](./ai_core/README.md)
