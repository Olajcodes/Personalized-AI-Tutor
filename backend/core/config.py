"""App configuration.

Logic:
- Loads environment variables for DB + JWT + runtime environment.
- Keep configuration minimal and explicit for MVP.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL")
    jwt_secret: str = os.getenv("JWT_SECRET")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    env: str = os.getenv("ENV")

settings = Settings()
