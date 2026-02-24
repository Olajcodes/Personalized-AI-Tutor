"""App configuration.

Logic:
- Loads environment variables for DB + JWT + runtime environment.
- Keep configuration minimal and explicit for MVP.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    env: str = os.getenv("ENV", "dev")

settings = Settings()
