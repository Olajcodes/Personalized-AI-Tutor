"""FastAPI entrypoint.

Logic:
- Wires routers under /api/v1
"""
from fastapi import FastAPI

from backend.endpoints.auth import router as auth_router
from backend.endpoints.lessons import router as lessons_router
from backend.endpoints.metadata import router as metadata_router
from backend.endpoints.student_learning_activity import learning_router, student_router
from backend.endpoints.students import router as students_router
from backend.endpoints.system import router as system_router
from backend.endpoints.topics import router as topics_router
from backend.endpoints.users import router as users_router

# Section 2 Routers
from backend.endpoints.tutor_sessions import router as tutor_sessions_router
from backend.endpoints.internal_postgres_service import router as internal_postgres_router

# Section 3 Routers (New)
from backend.endpoints.diagnostic import router as diagnostic_router
from backend.endpoints.learning_path import router as learning_path_router
from backend.endpoints.internal_graph import router as internal_graph_router

API_PREFIX = "/api/v1"

app = FastAPI(title="Mastery AI Backend", version="0.1.0")


# Register the routers
# This mounts the endpoints defined in your other files onto the app
app.include_router(learning_router, prefix=API_PREFIX)
app.include_router(student_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(lessons_router, prefix=API_PREFIX)
app.include_router(topics_router, prefix=API_PREFIX)
app.include_router(metadata_router, prefix=API_PREFIX)
app.include_router(students_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)

# Section 2 Router Wiring
app.include_router(tutor_sessions_router, prefix=API_PREFIX)
app.include_router(internal_postgres_router, prefix=API_PREFIX)

# Section 3 Router Wiring
app.include_router(diagnostic_router, prefix=API_PREFIX)
app.include_router(learning_path_router, prefix=API_PREFIX)
app.include_router(internal_graph_router, prefix=API_PREFIX)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "Welcome to the Personalized AI Tutor API. Visit /docs for interactive documentation."
    }
