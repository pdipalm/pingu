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