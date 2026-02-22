import uuid
from fastapi import APIRouter, HTTPException
from app.api.schemas import TargetOut
from app.repos.targets import fetch_all_targets, fetch_target_by_id

router = APIRouter()


@router.get("/targets", response_model=list[TargetOut])
def list_targets():
    return fetch_all_targets()


@router.get("/targets/{target_id}", response_model=TargetOut)
def get_target(target_id: uuid.UUID) -> TargetOut:
    row = fetch_target_by_id(target_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return TargetOut(**row)
