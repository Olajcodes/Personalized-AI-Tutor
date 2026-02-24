"""FastAPI entrypoint.

Logic:
- Wires routers under /api/v1
"""
from fastapi import FastAPI

from backend.endpoints.lessons import router as lessons_router
from backend.endpoints.topics import router as topics_router
from backend.endpoints.metadata import router as metadata_router
from backend.endpoints.tutor_session_and_chat_history2 import router as tutor_router

API_PREFIX = "/api/v1"

app = FastAPI(title="Mastery AI Backend", version="0.1.0")

app.include_router(lessons_router, prefix=API_PREFIX)
app.include_router(topics_router, prefix=API_PREFIX)
app.include_router(metadata_router, prefix=API_PREFIX)
app.include_router(tutor_router, prefix=API_PREFIX)