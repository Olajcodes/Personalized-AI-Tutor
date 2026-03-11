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
- PostgreSQL
- Qdrant
- Neo4j
- Redis (optional)

## Fresh Start (Local Installation)

Run from repository root unless stated otherwise.

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
```

- bash/zsh:
```bash
cp backend/.env.example backend/.env
cp ai_core/.env.example ai_core/.env
```

For frontend, create `frontend/.env` manually with your API base URL and auth keys required by the UI.

Set required secrets/URLs, especially:

- `backend/.env`
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `AI_CORE_BASE_URL` (local default: `http://127.0.0.1:10000`)
  - `CORS_ORIGINS` (include local frontend + production frontend domain)
- `ai_core/.env`
  - `GROQ_API_KEY` or `LLM_API_KEY`
  - `POSTGRES_DSN`
  - `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`
  - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `frontend/.env`
  - backend base URL and auth-related variables used by your UI.

### 5) Apply database migrations

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

### 6) One-time reset + ingest + auto-approve curriculum

This is the recommended clean baseline command.
It reseeds baseline curriculum entities, ingests all detected scopes from `docs/Curriculum_in_json` when available (otherwise `docs/SSS_NOTES_2026`),
auto-approves versions, and (optionally) reseeds Neo4j.

```powershell
python -m backend.scripts.reset_and_reseed_curriculum `
  --seed-reset `
  --no-seed-demo-learners `
  --no-disable-neo4j-sync `
  --seed-neo4j `
  --qdrant-batch-size 24 `
  --qdrant-timeout-seconds 240`
  --full-db-reset
  
```

Notes:

- LLM extraction/inference is enabled by default in this flow.
- The reset script now prefers canonical JSON curriculum under `docs/Curriculum_in_json` automatically when present.
- Use `--source-root <path>` to force a different corpus.
- If LLM is unavailable or output is invalid, ingestion falls back safely and logs fallback mode.
- Use `--disable-llm` only for deterministic fallback-only runs.
- Add `--full-db-reset` if you want to truncate all public application tables before reseeding.

### 7) Run services

Backend:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

AI Core:

```bash
python -m uvicorn ai_core.main:app --reload --port 10000
```

Frontend:

```bash
cd frontend
npm run dev
```

## Health Checks

- Backend Swagger: `http://127.0.0.1:8000/docs`
- Backend health: `http://127.0.0.1:8000/api/v1/system/health`
- AI Core health: `http://127.0.0.1:10000/health`

## Production Notes

- Keep `AI_CORE_ALLOW_FALLBACK=false` in strict production environments if you want hard failure when AI Core is unreachable.
- Configure `CORS_ORIGINS` explicitly; avoid `*` in production.
- Keep secrets only in secret managers (Render/CI/CD), not in git-tracked files.
- Keep curriculum ingestion and approval as an admin-only workflow.

## Deployment

The repository includes `render.yaml` for Render Blueprint deployment.

At minimum configure:

- Backend:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `AI_CORE_BASE_URL`
  - `CORS_ORIGINS`
- AI Core:
  - `GROQ_API_KEY` or `LLM_API_KEY`
  - datastore credentials (`POSTGRES_DSN`, `QDRANT_*`, `NEO4J_*`)

## Service-Specific Documentation

- Backend operations and API details: [backend/README.md](./backend/README.md)
- AI-core runtime and endpoints: [ai_core/README.md](./ai_core/README.md)
