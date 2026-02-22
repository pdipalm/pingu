import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import session_scope


def fetch_results_for_target(
    target_id: uuid.UUID,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 200,
    s: Session | None = None,
) -> list[dict]:
    where = ["target_id = :target_id"]
    limit = max(1, min(int(limit), 1000))
    params: dict = {"target_id": target_id, "limit": int(limit)}

    if since is not None:
        where.append("ts >= :since")
        params["since"] = since
    if until is not None:
        where.append("ts <= :until")
        params["until"] = until

    sql = f"""
        SELECT id, target_id, ts, success, latency_ms, status_code, error
        FROM probe_results
        WHERE {" AND ".join(where)}
        ORDER BY ts DESC
        LIMIT :limit
    """

    with session_scope(s) as session:
        rows = session.execute(text(sql), params).mappings().all()

    return [dict(r) for r in rows]


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
