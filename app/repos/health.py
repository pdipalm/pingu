from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import session_scope
from app.repos.util import timed_execute


@dataclass(frozen=True)
class HealthDbStats:
    enabled_targets: int
    max_interval_seconds: int
    last_result_ts: datetime | None


def db_ok(s: Session | None = None) -> bool:
    try:
        with session_scope(existing=s) as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def fetch_health_db_stats(s: Session | None = None) -> HealthDbStats:
    with session_scope(existing=s) as session:
        enabled_targets = timed_execute(
            session,
            text("SELECT COUNT(*) FROM targets WHERE enabled = true"),
            None,
            label="fetch_enabled_targets_count",
        ).scalar_one()

        max_interval_seconds = timed_execute(
            session,
            text("SELECT COALESCE(MAX(interval_seconds), 0) FROM targets WHERE enabled = true"),
            None,
            label="fetch_max_interval_seconds",
        ).scalar_one()

        last_ts = timed_execute(
            session,
            text("SELECT MAX(ts) FROM probe_results"),
            None,
            label="fetch_last_result_ts",
        ).scalar_one()

    return HealthDbStats(
        enabled_targets=int(enabled_targets),
        max_interval_seconds=int(max_interval_seconds),
        last_result_ts=last_ts,
    )
