
from app.db import SessionLocal
from app.models import IcmpTarget, HttpTarget
from sqlalchemy import text

def fetch_enabled_icmp_targets() -> list[IcmpTarget]:
    with SessionLocal() as s:
        rows = s.execute(
            text(
                """
                SELECT id, name, host, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'icmp'
                """
            )
        ).mappings().all()

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


def fetch_enabled_http_targets() -> list[HttpTarget]:
    with SessionLocal() as s:
        rows = s.execute(
            text(
                """
                SELECT id, name, url, interval_seconds, timeout_ms
                FROM targets
                WHERE enabled = true AND type = 'http'
                """
            )
        ).mappings().all()

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
