"""Auth endpoints (stub wiring for MVP)."""

from fastapi import APIRouter
from backend.schemas.auth_schema import RegisterIn, LoginIn, AuthOut
from backend.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(payload: RegisterIn):
    # TODO: store user + hashed password in Postgres
    return {"message": "stub: user created"}

@router.post("/login", response_model=AuthOut)
def login(payload: LoginIn):
    # TODO: validate user/password from Postgres
    token = create_access_token(subject=payload.email, role="student")
    return AuthOut(access_token=token, role="student")
