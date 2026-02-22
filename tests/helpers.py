# tests/db_helpers.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

DEFAULT_HOST = "127.0.0.1"
DEFAULT_INTERVAL = 30
DEFAULT_TIMEOUT_MS = 1000


def insert_target(
    s: Session,
    *,
    tid: UUID,
    name: str,
    type_: str = "icmp",
    host: Optional[str] = DEFAULT_HOST,
    url: Optional[str] = None,
    interval_seconds: int = DEFAULT_INTERVAL,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    enabled: bool = True,
) -> None:
    """
    Insert a row into targets. Does not commit.
    """
    s.execute(
        text("""
            INSERT INTO targets
              (id, name, type, host, url, interval_seconds, timeout_ms, enabled, created_at, updated_at)
            VALUES
              (:id, :name, :type, :host, :url, :interval_seconds, :timeout_ms, :enabled, NOW(), NOW())
            """),
        {
            "id": str(tid),
            "name": name,
            "type": type_,
            "host": host,
            "url": url,
            "interval_seconds": interval_seconds,
            "timeout_ms": timeout_ms,
            "enabled": enabled,
        },
    )


def insert_result(
    s: Session,
    *,
    target_id: UUID,
    ts: datetime,
    success: bool = True,
    latency_ms: Optional[int] = 10,
    status_code: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """
    Insert a row into probe_results. Does not commit.
    """
    s.execute(
        text("""
            INSERT INTO probe_results
              (target_id, ts, success, latency_ms, status_code, error)
            VALUES
              (:target_id, :ts, :success, :latency_ms, :status_code, :error)
            """),
        {
            "target_id": str(target_id),
            "ts": ts,
            "success": success,
            "latency_ms": latency_ms,
            "status_code": status_code,
            "error": (error[:500] if error else None),
        },
    )


def seed_basic_targets_and_results(
    s: Session,
    *,
    now: datetime,
    enabled_count: int = 2,
    include_disabled: bool = True,
) -> dict[str, UUID]:
    """
    Convenience seeder for API tests.
    Returns ids by name.
    """
    from uuid import uuid4

    ids: dict[str, UUID] = {}

    # Enabled ICMP target
    t1 = uuid4()
    insert_target(s, tid=t1, name="t-icmp-1", type_="icmp", enabled=True)
    insert_result(s, target_id=t1, ts=now, success=True, latency_ms=12)
    ids["t-icmp-1"] = t1

    # Enabled HTTP target
    t2 = uuid4()
    insert_target(
        s, tid=t2, name="t-http-1", type_="http", host=None, url="https://example.com", enabled=True
    )
    insert_result(s, target_id=t2, ts=now, success=True, latency_ms=120, status_code=200)
    ids["t-http-1"] = t2

    if include_disabled:
        td = uuid4()
        insert_target(s, tid=td, name="t-disabled", type_="icmp", enabled=False)
        insert_result(s, target_id=td, ts=now, success=True, latency_ms=1)
        ids["t-disabled"] = td

    return ids
