# Mastery AI Backend (FastAPI) — Simplified MVP Structure

This backend is organized for fast parallel development for the **Mastery AI** MVP.

## Key folders
- **endpoints/**: FastAPI routers (HTTP layer only)
- **services/**: Business logic (validation + orchestration)
- **repositories/**: Database access (SQLAlchemy queries only)
- **models/**: SQLAlchemy ORM models (Postgres)
- **schemas/**: Pydantic request/response models
- **core/**: config, database, security utilities
- **tests/**: unit tests

## Run (local)
1. Create a venv and install deps
2. Copy `.env.example` → `.env`
3. Run: `uvicorn backend.main:app --reload`

Generated: 2026-02-23
