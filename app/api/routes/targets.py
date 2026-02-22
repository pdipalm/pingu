import uuid
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.api.schemas import TargetOut
from app.repos.targets import fetch_all_targets, fetch_target_by_id

router = APIRouter()


class TargetsListOut(BaseModel):
    items: list[TargetOut]


@router.get("/targets", response_model=TargetsListOut)
def list_targets(
    status: Literal["enabled", "disabled", "all"] = Query("enabled"),
):
    rows = fetch_all_targets(status=status)
    return {"items": [TargetOut(**r) for r in rows]}


@router.get("/targets/{target_id}", response_model=TargetOut)
def get_target(target_id: uuid.UUID) -> TargetOut:
    row = fetch_target_by_id(target_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetOut(**row)
