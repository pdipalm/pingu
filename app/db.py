from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# Create one Engine per process. This is fine for your api + poller containers.
# NOTE: Your DATABASE_URL is using SQLAlchemy URL style: postgresql+psycopg://...
engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # avoids stale connections
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope(existing: Session | None = None):
    if existing is not None:
        yield existing
        return

    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def db_ok() -> bool:
    """
    Lightweight connectivity check for /health.
    Returns True if we can connect and run `SELECT 1`.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
