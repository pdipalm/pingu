import uuid
from sqlalchemy.orm import Session
from app.db import session_scope
from app.models import IcmpTarget, HttpTarget
from sqlalchemy import text


def fetch_all_targets(
    status: str = "enabled",
    s: Session | None = None,
) -> list[dict]:
    where_sql = ""
    params: dict = {}

    if status == "enabled":
        where_sql = "WHERE enabled = true"
    elif status == "disabled":
        where_sql = "WHERE enabled = false"
    elif status == "all":
        where_sql = ""
    else:
        # Should be impossible if API layer uses Literal, but keeps this safe if reused elsewhere
        raise ValueError("Invalid status. Must be one of: enabled, disabled, all")

    sql = f"""
        SELECT id, name, type, enabled, interval_seconds, timeout_ms, host, url
        FROM targets
        {where_sql}
        ORDER BY name
    """

    with session_scope(s) as session:
        rows = session.execute(text(sql), params).mappings().all()

    return [dict(r) for r in rows]


def fetch_target_by_id(target_id: uuid.UUID, s: Session | None = None) -> dict | None:
    with session_scope(s) as session:
        row = (
            session.execute(
                text(
                    """
                SELECT id, name, type, enabled, interval_seconds, timeout_ms, host, url
                FROM targets
                WHERE id = :id
                """
                ),
                {"id": target_id},
            )
            .mappings()
            .one_or_none()
        )

    return dict(row) if row is not None else None


def fetch_enabled_icmp_targets(s: Session | None = None) -> list[IcmpTarget]:
    with session_scope(s) as session:
        rows = (
            session.execute(
                text(
                    """
                SELECT id, name, host, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'icmp'
                """
                )
            )
            .mappings()
            .all()
        )

    out: list[IcmpTarget] = []
    for r in rows:
        host = r["host"]
        if host is None:
            # Shouldn't happen due to DB CHECK constraint, but keeps type checkers happy
            continue
        out.append(
            IcmpTarget(
                id=r["id"],
                name=r["name"],
                host=host,
                interval_seconds=int(r["interval_seconds"]),
                timeout_ms=int(r["timeout_ms"]),
            )
        )
    return out


def fetch_enabled_http_targets(s: Session | None = None) -> list[HttpTarget]:
    with session_scope(s) as session:
        rows = (
            session.execute(
                text(
                    """
                SELECT id, name, url, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'http'
                """
                )
            )
            .mappings()
            .all()
        )

    out: list[HttpTarget] = []
    for r in rows:
        url = r["url"]
        if url is None:
            continue

        out.append(
            HttpTarget(
                id=r["id"],
                name=r["name"],
                url=url,
                interval_seconds=int(r["interval_seconds"]),
                timeout_ms=int(r["timeout_ms"]),
            )
        )

    return out
