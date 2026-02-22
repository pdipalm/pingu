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
