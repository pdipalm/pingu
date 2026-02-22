from sqlalchemy.orm import Session
from app.db import session_scope
from app.models import IcmpTarget, HttpTarget
from sqlalchemy import text


def fetch_all_targets(s: Session | None = None) -> list[dict]:
    with session_scope(s) as session:
        rows = session.execute(text("""
                SELECT id, name, type, enabled, interval_seconds, timeout_ms, host, url
                FROM targets
                ORDER BY name
            """)).mappings().all()
    return [dict(r) for r in rows]


def fetch_enabled_icmp_targets(s: Session | None = None) -> list[IcmpTarget]:
    with session_scope(s) as session:
        rows = session.execute(text("""
                SELECT id, name, host, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'icmp'
                """)).mappings().all()

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
        rows = session.execute(text("""
                SELECT id, name, url, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'http'
                """)).mappings().all()

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
