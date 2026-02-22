from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # avoids stale connections
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def session_scope(existing: Session | None = None):
    """
    Yields a Session.

    - If `existing` is provided, participates in the caller's transaction and does not
      commit/rollback/close.
    - If `existing` is None, opens a new session and manages commit/rollback/close.
    """
    if existing is not None:
        yield existing
        return

    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
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
