from __future__ import annotations

from fastapi import APIRouter

from api.dynamic_scheduler import DynamicScheduler


router = APIRouter()
scheduler = DynamicScheduler()


@router.get("/ops/scheduler/preview")
def scheduler_preview(limit: int = 50) -> dict:
    return scheduler.preview(limit=limit)


@router.post("/ops/scheduler/reprioritize")
def scheduler_reprioritize() -> dict:
    return scheduler.reprioritize()
