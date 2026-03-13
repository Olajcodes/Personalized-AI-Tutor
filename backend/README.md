# Mastery AI Backend

FastAPI backend service for authentication, student onboarding, curriculum delivery,
assessment orchestration, governance workflows, and persistence.

## Runtime Summary

- Framework: FastAPI
- ORM/Migrations: SQLAlchemy + Alembic
- Database: PostgreSQL
- Vector store integration: Qdrant
- Graph integration: Neo4j
- Auth: JWT

## Environment

Create `backend/.env` from `backend/.env.example`.

Minimum required for local run:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/mastery_ai
JWT_SECRET=change_me
AI_CORE_BASE_URL=http://127.0.0.1:10000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000
INTERNAL_SERVICE_KEY=replace_with_shared_secret
```

Recommended graph/vector/LLM ingestion settings:

```env
QDRANT_URL=<your-qdrant-url>
QDRANT_API_KEY=<your-qdrant-api-key>
QDRANT_COLLECTION=MasteryAI
QDRANT_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-neo4j-password>
USE_NEO4J_GRAPH=true

LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=<your-groq-key>
CURRICULUM_CONCEPT_USE_LLM=true
CURRICULUM_CONCEPT_EXTRACT_USE_LLM=true
CURRICULUM_PREREQ_USE_LLM=true
```

Prewarm queue/worker defaults:

```env
PREWARM_QUEUE_ENABLED=true
PREWARM_WORKER_ENABLED=true
PREWARM_WORKER_POLL_SECONDS=5
PREWARM_WORKER_BATCH_SIZE=3
```

## Installation

From repository root:

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
```

## Database Migration

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m alembic -c backend/alembic.ini current
```

## Fresh Start Data Bootstrap (Recommended)

This one command:

- seeds baseline curriculum entities,
- clears old curriculum ingestion/version rows,
- clears Qdrant curriculum vectors,
- ingests all discovered scopes from `docs/Curriculum_in_json` when available, otherwise falls back to `docs/SSS_NOTES_2026`,
- auto-approves ingested versions,
- optionally reseeds Neo4j topic/concept graph.

```powershell
python -m backend.scripts.reset_and_reseed_curriculum `
  --seed-reset `
  --no-seed-demo-learners `
  --no-disable-neo4j-sync `
  --seed-neo4j `
  --qdrant-batch-size 24 `
  --qdrant-timeout-seconds 240
```

Important:

- LLM-first extraction/inference is enabled by default in this script.
- Curriculum reset now prefers canonical topic JSON from `docs/Curriculum_in_json` automatically when that folder contains `.json` files.
- Override with `--source-root <path>` if you want to ingest a different source corpus explicitly.
- If LLM fails or returns invalid output, ingestion falls back automatically and logs fallback mode.
- Add `--disable-llm` for deterministic fallback-only ingestion.
- Add `--seed-demo-learners` only if you explicitly want demo learner rows.
- Demo learner seed now creates identities/profile scope only. It does not fabricate concept mastery; mastery should come from diagnostics, quizzes, and tutor evidence.
- Add `--full-db-reset` to wipe all public application tables (except `alembic_version`) before reseeding.

## Run Backend

From repository root:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Swagger:

- `http://127.0.0.1:8000/docs`

Health:

- `http://127.0.0.1:8000/api/v1/system/health`

The backend health payload now includes:

- `checks.internal_service_auth`
- `checks.prewarm_queue`

## API Surface (Base Prefix: `/api/v1`)

Major route groups:

- Auth: `/auth/*`
- Users/Profile: `/users/*`, `/students/*`
- Learning: `/learning/*`
- Tutor: `/tutor/*`
- Teacher: `/teachers/*`
- Admin curriculum/governance: `/admin/*`
- Internal adapters: `/internal/*`

## LLM/Fallback Audit Logging

Ingestion job logs include explicit mode and fallback flags per file/topic:

- `concept_extraction_mode`
- `prereq_inference_mode`
- `concept_fallback_used`
- `prereq_fallback_used`
- `stage = "llm_fallback"` entries when fallback occurs

Quick SQL inspection:

```sql
SELECT j.id,
       log->>'stage' AS stage,
       log->>'message' AS message,
       log->'extra' AS extra
FROM curriculum_ingestion_jobs j
CROSS JOIN LATERAL jsonb_array_elements((j.logs_payload)::jsonb) AS log
WHERE log->>'stage' IN ('extraction_mode', 'llm_fallback', 'prereq_inference')
ORDER BY j.created_at DESC;
```

## Common Issues

1. `404 /students/profile` after login:
- Profile setup not completed for that authenticated user.
- Complete onboarding via `POST /api/v1/students/profile/setup`.

2. Qdrant timeout during ingestion:
- Reduce batch size and/or increase timeout.
- Example: `--qdrant-batch-size 24 --qdrant-timeout-seconds 240`.

3. Neo4j connection errors:
- Verify `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.
- Disable graph usage temporarily with `USE_NEO4J_GRAPH=false`.

4. Supabase/Postgres DNS/connection failures:
- Verify `DATABASE_URL` host and SSL mode.
- For Supabase pooler, use `?sslmode=require`.

5. Internal adapter calls returning `401` or `503`:
- Ensure the same `INTERNAL_SERVICE_KEY` is set in both `backend/.env` and `ai_core/.env`.
- `401` means the key is missing or mismatched.
- `503` means the backend internal auth was not configured at all.

6. Prewarm queue not moving:
- Check `GET /api/v1/system/health` and inspect `checks.prewarm_queue`.
- Ensure `PREWARM_QUEUE_ENABLED=true` and `PREWARM_WORKER_ENABLED=true`.
- If you deploy multiple backend instances, each instance can run the in-process worker. Keep batch size conservative.

## Production Guidance

- Set strict `CORS_ORIGINS` (no wildcard).
- Keep `JWT_SECRET` and DB keys in secret manager.
- Keep `INTERNAL_SERVICE_KEY` identical across backend and ai-core.
- Restrict admin endpoints to authorized users only.
- Keep ingestion/approval workflows auditable via job logs.
- Keep `PREWARM_QUEUE_ENABLED=true` if you want durable warm jobs. Disable only for debugging.
