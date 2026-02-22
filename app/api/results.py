from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import (
    LatestResultByTargetItem,
    ProbeResultOut,
    TargetResultsResponse,
    LatestResultByTargetResponse,
)
from app.repos.results import fetch_latest_result_by_target, fetch_results_for_target
from app.repos.targets import fetch_target_by_id

router = APIRouter()

DEFAULT_LIMIT = 200
MAX_LIMIT = 1000


@router.get("/results/latest-by-target", response_model=LatestResultByTargetResponse)
def get_latest_result_by_target() -> LatestResultByTargetResponse:
    rows = fetch_latest_result_by_target()
    return LatestResultByTargetResponse(
        items=[LatestResultByTargetItem(**r) for r in rows]
    )


@router.get("/targets/{target_id}/results", response_model=TargetResultsResponse)
def get_target_results(
    target_id: uuid.UUID,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> TargetResultsResponse:
    t = fetch_target_by_id(target_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Target not found")

    # Optional: validate ranges
    if since is not None and until is not None and since > until:
        raise HTTPException(status_code=400, detail="since must be <= until")

    results = fetch_results_for_target(
        target_id,
        since=since,
        until=until,
        limit=limit,
    )
    return TargetResultsResponse(
        target_id=t["id"],
        target_name=t["name"],
        items=[ProbeResultOut(**r) for r in results],
    )
