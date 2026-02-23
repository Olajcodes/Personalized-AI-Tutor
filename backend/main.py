"""FastAPI entrypoint.

Logic:
- Wires routers under /api/v1
"""

from fastapi import FastAPI
from backend.endpoints import auth, lessons, system

API_PREFIX = "/api/v1"

app = FastAPI(title="Mastery AI Backend", version="0.1.0")

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(lessons.router, prefix=API_PREFIX)
app.include_router(system.router, prefix=API_PREFIX)
