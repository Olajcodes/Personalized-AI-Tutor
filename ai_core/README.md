# Mastery AI Core

`ai_core` is the orchestration service for tutoring and quiz intelligence.
It exposes HTTP endpoints consumed by the backend.

## Responsibilities

- Tutor response generation (chat, hint, explain-mistake)
- Quiz generation and quiz insights
- Safety checks (basic moderation and prompt-injection hygiene)
- Retrieval orchestration hooks (with backend/internal retrieval integration)

## Service Endpoints

- `GET /` -> service status
- `GET /health` -> configuration health checks
- `POST /tutor/chat`
- `POST /tutor/hint`
- `POST /tutor/explain-mistake`
- `POST /quiz/generate`
- `GET /quiz/{quiz_id}/attempt/{attempt_id}/insights`

## Environment

Create `ai_core/.env` from `ai_core/.env.example`.

Minimum local configuration:

```env
PORT=10000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=<your-groq-key>

POSTGRES_DSN=postgresql://postgres:password@localhost:5432/mastery_ai
QDRANT_URL=<your-qdrant-url>
QDRANT_API_KEY=<your-qdrant-api-key>
QDRANT_COLLECTION=MasteryAI

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-neo4j-password>
```

Notes:

- `POSTGRES_DSN` is preferred.
- If `POSTGRES_DSN` is missing, service can fall back to `DATABASE_URL`.
- `BACKEND_INTERNAL_RAG_URL` should point to backend internal RAG endpoint if used:
  - `http://127.0.0.1:8000/api/v1/internal/rag/retrieve`

## Installation

From repository root:

```bash
python -m venv .venv
```

Activate environment, then:

```bash
python -m pip install --upgrade pip
python -m pip install -r ai_core/requirements.txt
```

## Run

From repository root:

```bash
python -m uvicorn ai_core.main:app --reload --port 10000
```

Health check:

- `http://127.0.0.1:10000/health`

## Backend Integration

Backend should point to ai-core with:

```env
AI_CORE_BASE_URL=http://127.0.0.1:10000
```

## Production Guidance

- Use strict CORS allowlist.
- Keep API keys in deployment secret manager.
- Pin model names explicitly per environment.
- Monitor `/health` plus backend `/api/v1/system/health` for cross-service issues.
