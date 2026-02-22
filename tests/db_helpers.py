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
