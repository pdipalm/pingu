import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import session_scope


def insert_probe_result(
    *,
    target_id: uuid.UUID,
    ts: datetime,
    success: bool,
    latency_ms: int | None,
    status_code: int | None,
    error: str | None,
    s: Session | None = None,
) -> None:
    owns_session = s is None
    with session_scope(s) as session:
        session.execute(
            text("""
                INSERT INTO probe_results (target_id, ts, success, latency_ms, status_code, error)
                VALUES (:target_id, :ts, :success, :latency_ms, :status_code, :error)
                """),
            {
                "target_id": target_id,
                "ts": ts,
                "success": success,
                "latency_ms": latency_ms,
                "status_code": status_code,
                "error": error,
            },
        )
        if owns_session:
            session.commit()
