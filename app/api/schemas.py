import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class HealthThresholds(BaseModel):
    stale_after_seconds: int = Field(..., ge=0)


class HealthStats(BaseModel):
    enabled_targets: int = Field(..., ge=0)
    last_result_ts: datetime | None = None
    seconds_since_last_result: int | None = Field(default=None, ge=0)


class HealthResponse(BaseModel):
    ok: bool
    db: bool
    thresholds: HealthThresholds
    stats: HealthStats


class TargetOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    enabled: bool
    interval_seconds: int = Field(..., ge=1)
    timeout_ms: int = Field(..., ge=1)
    host: str | None = None
    url: str | None = None


class ProbeResultOut(BaseModel):
    id: int
    target_id: uuid.UUID
    ts: datetime
    success: bool
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None


class TargetResultsResponse(BaseModel):
    target_id: uuid.UUID
    target_name: str
    items: list[ProbeResultOut]


class LatestResultByTargetItem(BaseModel):
    target_id: uuid.UUID
    target_name: str
    ts: datetime | None = None
    success: bool | None = None
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None


class LatestResultItem(BaseModel):
    target_id: uuid.UUID
    target_name: str
    ts: datetime
    success: bool
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None


class LatestResultsResponse(BaseModel):
    items: list[LatestResultItem]


class LatestResultByTargetResponse(BaseModel):
    items: list[LatestResultByTargetItem]
