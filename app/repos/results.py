import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import DEFAULT_LIMIT, MAX_LIMIT
from app.db import session_scope


def fetch_latest_results(
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = DEFAULT_LIMIT,
    s: Session | None = None,
) -> list[dict]:
    limit = max(1, min(int(limit), MAX_LIMIT))

    where_clauses: list[str] = []
    params: dict = {"limit": limit}

    if since is not None:
        where_clauses.append("r.ts >= :since")
        params["since"] = since

    if until is not None:
        # exclusive upper bound to avoid double-counting when paging by time
        where_clauses.append("r.ts < :until")
        params["until"] = until

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
        SELECT
            r.target_id,
            t.name AS target_name,
            r.ts,
            r.success,
            r.latency_ms,
            r.status_code,
            r.error
        FROM probe_results r
        JOIN targets t ON t.id = r.target_id
        {where_sql}
        ORDER BY r.ts DESC, r.id DESC
        LIMIT :limit
    """

    with session_scope(s) as session:
        rows = session.execute(text(sql), params).mappings().all()

    return [dict(r) for r in rows]


def fetch_latest_result_by_target(
    enabled_only: bool = True,
    s: Session | None = None,
) -> list[dict]:
    sql = f"""
        SELECT
            t.id AS target_id,
            t.name AS target_name,
            r.ts,
            r.success,
            r.latency_ms,
            r.status_code,
            r.error
        FROM targets t
        LEFT JOIN LATERAL (
            SELECT ts, success, latency_ms, status_code, error
            FROM probe_results
            WHERE target_id = t.id
            ORDER BY ts DESC
            LIMIT 1
        ) r ON true
        WHERE (:enabled_only = false OR t.enabled = true)
        ORDER BY t.name
        """
    with session_scope(s) as session:
        rows = (
            session.execute(text(sql), {"enabled_only": enabled_only}).mappings().all()
        )

    return [dict(r) for r in rows]


def fetch_results_for_target(
    target_id: uuid.UUID,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = DEFAULT_LIMIT,
    s: Session | None = None,
) -> list[dict]:
    where = ["target_id = :target_id"]
    limit = max(1, min(int(limit), MAX_LIMIT))
    params: dict = {"target_id": target_id, "limit": int(limit)}

    if since is not None:
        where.append("ts >= :since")
        params["since"] = since
    if until is not None:
        where.append("ts < :until")
        params["until"] = until

    sql = f"""
        SELECT id, target_id, ts, success, latency_ms, status_code, error
        FROM probe_results
        WHERE {" AND ".join(where)}
        ORDER BY ts DESC, id DESC
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
