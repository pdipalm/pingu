"""Pydantic response schemas used by the API.

All timestamps in these schemas are timezone-aware and use UTC.
This module centralizes the output shapes for health checks, targets,
and probe results returned by the HTTP API.
"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    This helper is used as a `default_factory` for `datetime` fields so
    responses consistently carry UTC timestamps.
    """
    return datetime.now(timezone.utc)


class HealthThresholds(BaseModel):
    """Threshold configuration used by the health endpoint.

    Attributes:
    - `stale_after_seconds`: number of seconds without a result before a
        target is considered stale.
    """

    stale_after_seconds: int = Field(..., ge=0)


class HealthStats(BaseModel):
    """Runtime statistics about probe execution.

    Attributes:
    - `enabled_targets`: count of targets currently enabled for probing.
    - `last_result_ts`: timestamp of the most recent probe result, or
        `None` when no results exist yet.
    - `seconds_since_last_result`: seconds since `last_result_ts`, or
        `None` when `last_result_ts` is `None`.
    """

    enabled_targets: int = Field(..., ge=0)
    last_result_ts: datetime | None = None
    seconds_since_last_result: int | None = Field(default=None, ge=0)


class HealthResponse(BaseModel):
    """Response payload for the `/health` endpoint.

    Attributes:
    - `generated_at`: when the response was produced (UTC).
    - `ok`: overall health boolean.
    - `db`: whether the database is reachable.
    - `thresholds`: the configured health thresholds.
    - `stats`: runtime health statistics.
    """

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ok: bool
    db: bool
    thresholds: HealthThresholds
    stats: HealthStats


class TargetResponse(BaseModel):
    """Representation of a configured monitoring target.

    Attributes mirror the stored target configuration and include fields
    relevant for probing such as `interval_seconds` and `timeout_ms`.
    Depending on `type`, either `host` or `url` will be populated.
    """

    id: uuid.UUID
    name: str
    type: str
    enabled: bool
    interval_seconds: int = Field(..., ge=1)
    timeout_ms: int = Field(..., ge=1)
    host: str | None = None
    url: str | None = None


class TargetListResponse(BaseModel):
    """List response for available targets.

    - `generated_at`: UTC timestamp when the list was generated.
    - `items`: the list of `TargetResponse` items.
    """

    generated_at: datetime = Field(default_factory=utcnow)
    items: list[TargetResponse]


class ProbeResultOut(BaseModel):
    """Serialized probe result returned by result endpoints.

    Fields include timing, status, and optional error information.
    """

    id: int
    target_id: uuid.UUID
    ts: datetime
    success: bool
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None


class TargetResultsResponse(BaseModel):
    """Results for a single target.

    - `target_id`/`target_name`: identify the target.
    - `generated_at`: when this response was produced (UTC).
    - `items`: list of `ProbeResultOut` entries ordered by time.
    """

    target_id: uuid.UUID
    target_name: str
    generated_at: datetime = Field(default_factory=utcnow)
    items: list[ProbeResultOut]


class LatestResultByTargetItem(BaseModel):
    """Latest result summary for a given target.

    Fields may be `None` when no result exists yet for the target.
    """

    target_id: uuid.UUID
    target_name: str
    ts: datetime | None = None
    success: bool | None = None
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None


class LatestResultItem(BaseModel):
    """A single latest result entry for listing recent probe results.

    Unlike `LatestResultByTargetItem`, fields here are expected to be
    populated since this model represents an actual recorded result.
    """

    target_id: uuid.UUID
    target_name: str
    ts: datetime
    success: bool
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None


class LatestResultsResponse(BaseModel):
    """Response that lists the most recent probe results across targets.

    - `generated_at`: UTC timestamp for the response.
    - `items`: list of `LatestResultItem` entries.
    """

    generated_at: datetime = Field(default_factory=utcnow)
    items: list[LatestResultItem]


class LatestResultByTargetResponse(BaseModel):
    """Latest result per-target summary response.

    - `generated_at`: UTC timestamp for the response.
    - `items`: list of `LatestResultByTargetItem` entries describing
        each target's most recent result (or `None` if none exists).
    """

    generated_at: datetime = Field(default_factory=utcnow)
    items: list[LatestResultByTargetItem]
