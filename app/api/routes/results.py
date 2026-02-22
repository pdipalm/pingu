from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from app.api.schemas import (
    LatestResultByTargetItem,
    LatestResultByTargetResponse,
    LatestResultItem,
    LatestResultsResponse,
)
from app.constants import DEFAULT_LIMIT, MAX_LIMIT
from app.repos.results import fetch_latest_result_by_target, fetch_latest_results

router = APIRouter()


@router.get(
    "/results/latest",
    summary="Get the latest results",
    description="Get the latest results from the poller. You can filter results by a time range using the `since` and `until` query parameters.",
    response_model=LatestResultsResponse,
)
def get_latest_result(
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> LatestResultsResponse:
    rows = fetch_latest_results(since=since, until=until, limit=limit)
    return LatestResultsResponse(items=[LatestResultItem(**r) for r in rows])


@router.get(
    "/results/latest-by-target",
    summary="Get the latest result by target",
    description="Get the latest result from each target.",
    response_model=LatestResultByTargetResponse,
)
def get_latest_result_by_target() -> LatestResultByTargetResponse:
    rows = fetch_latest_result_by_target()
    return LatestResultByTargetResponse(
        items=[LatestResultByTargetItem(**r) for r in rows]
    )
