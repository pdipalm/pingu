from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import session_scope


@dataclass(frozen=True)
class HealthDbStats:
    enabled_targets: int
    max_interval_seconds: int
    last_result_ts: datetime | None


def fetch_health_db_stats(s: Session | None = None) -> HealthDbStats:
    with session_scope(s) as session:
        enabled_targets = session.execute(
            text("SELECT COUNT(*) FROM targets WHERE enabled = true")
        ).scalar_one()

        max_interval_seconds = session.execute(
            text(
                "SELECT COALESCE(MAX(interval_seconds), 0) "
                "FROM targets WHERE enabled = true"
            )
        ).scalar_one()

        last_ts = session.execute(
            text("SELECT MAX(ts) FROM probe_results")
        ).scalar_one()

    return HealthDbStats(
        enabled_targets=int(enabled_targets),
        max_interval_seconds=int(max_interval_seconds),
        last_result_ts=last_ts,
    )