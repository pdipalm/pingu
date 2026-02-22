import uuid
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from app.api.schemas import TargetListResponse, TargetResponse
from app.repos.targets import fetch_all_targets, fetch_target_by_id

router = APIRouter()


@router.get("/targets", response_model=TargetListResponse)
def list_targets(
    status: Literal["enabled", "disabled", "all"] = Query("enabled"),
):
    rows = fetch_all_targets(status=status)
    return {"items": [TargetResponse(**r) for r in rows]}


@router.get("/targets/{target_id}", response_model=TargetResponse)
def get_target(target_id: uuid.UUID) -> TargetResponse:
    row = fetch_target_by_id(target_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetResponse(**row)
