"""Database setup (SQLAlchemy).

Logic:
- Creates SQLAlchemy engine and session factory.
- Provides get_db() dependency for FastAPI endpoints.
"""

from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings


_connect_args = {}
_is_supabase_pooler = False
try:
    _parsed_db_url = urlsplit(settings.database_url)
    _is_supabase_pooler = (
        (_parsed_db_url.hostname or "").endswith(".supabase.com") and _parsed_db_url.port == 6543
    )
except ValueError:
    _is_supabase_pooler = False

if settings.database_url.startswith("postgresql"):
    _connect_args = {
        # Fail fast on broken network paths instead of hanging request handlers.
        "connect_timeout": settings.db_connect_timeout_seconds,
        "keepalives": 1,
        "keepalives_idle": settings.db_keepalives_idle_seconds,
        "keepalives_interval": settings.db_keepalives_interval_seconds,
        "keepalives_count": settings.db_keepalives_count,
    }

if _is_supabase_pooler:
    # Supabase transaction pooler already pools connections.
    # Disabling SQLAlchemy pool avoids stale pooled sockets on long-lived dev servers.
    engine = create_engine(
        settings.database_url,
        connect_args=_connect_args,
        poolclass=NullPool,
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
        connect_args=_connect_args,
    )
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
