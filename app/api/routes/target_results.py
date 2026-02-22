from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import ProbeResultOut, TargetResultsResponse
from app.constants import DEFAULT_LIMIT, MAX_LIMIT
from app.repos.results import fetch_results_for_target
from app.repos.targets import fetch_target_by_id

router = APIRouter()


@router.get(
    "/targets/{target_id}/results",
    summary="Get results for a specific target",
    description="Get the results for a specific target. You can filter results by a time range using the `since` and `until` query parameters.",
    response_model=TargetResultsResponse,
)
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
