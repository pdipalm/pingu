from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.schemas import HealthResponse, HealthStats, HealthThresholds
from app.db import SessionLocal, db_ok
from app.repos.health import fetch_health_db_stats

router = APIRouter()

STALE_GRACE_MULT = 1.5
MIN_STALE_SECONDS = 30


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db = db_ok()
    if not db:
        return HealthResponse(
            ok=False,
            db=False,
            thresholds=HealthThresholds(stale_after_seconds=0),
            stats=HealthStats(
                enabled_targets=0,
                last_result_ts=None,
                seconds_since_last_result=None,
            ),
        )

    now = datetime.now(timezone.utc)

    with SessionLocal() as s:
        db_stats = fetch_health_db_stats(s)

        enabled_targets = db_stats.enabled_targets
        max_interval = db_stats.max_interval_seconds
        last_ts = db_stats.last_result_ts

        seconds_since = None
        if last_ts is not None:
            last_ts = last_ts.astimezone(timezone.utc)
            seconds_since = int((now - last_ts).total_seconds())

        stale_after_s = 0
        if enabled_targets > 0 and max_interval > 0:
            stale_after_s = max(
                MIN_STALE_SECONDS,
                int(math.ceil(max_interval * STALE_GRACE_MULT)),
            )

    ok = True
    if (
        enabled_targets > 0
        and seconds_since is not None
        and seconds_since > stale_after_s
    ):
        ok = False

    return HealthResponse(
        ok=ok,
        db=True,
        thresholds=HealthThresholds(stale_after_seconds=stale_after_s),
        stats=HealthStats(
            enabled_targets=enabled_targets,
            last_result_ts=last_ts,
            seconds_since_last_result=seconds_since,
        ),
    )
