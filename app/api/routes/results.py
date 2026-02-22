from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.schemas import (
    LatestResultByTargetItem,
    LatestResultByTargetResponse,
    LatestResultItem,
    LatestResultsResponse,
)
from app.repos.results import (
    fetch_latest_result_by_target,
    fetch_latest_results,
)
from app.api.constants import DEFAULT_LIMIT, MAX_LIMIT

router = APIRouter()


@router.get("/results/latest", response_model=LatestResultsResponse)
def get_latest_result(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> LatestResultsResponse:
    rows = fetch_latest_results(limit=limit)
    return LatestResultsResponse(items=[LatestResultItem(**r) for r in rows])


@router.get("/results/latest-by-target", response_model=LatestResultByTargetResponse)
def get_latest_result_by_target() -> LatestResultByTargetResponse:
    rows = fetch_latest_result_by_target()
    return LatestResultByTargetResponse(
        items=[LatestResultByTargetItem(**r) for r in rows]
    )
