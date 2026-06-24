from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.foundation_job_store import FoundationJobStore

router = APIRouter(prefix="/foundation/jobs", tags=["foundation-jobs"])
foundation_jobs = FoundationJobStore()


class FoundationJobRequest(BaseModel):
    model: dict[str, Any] = Field(default_factory=lambda: {"model_id": "ailovanta-owned", "target_version": "candidate", "parameter_count_b": 1.0})
    dataset_shards: list[dict[str, Any]]
    nodes: list[dict[str, Any]]
    stage: Literal["pretrain", "continue_pretrain", "sft", "preference", "eval"] = "pretrain"
    max_steps: int = Field(default=1000, ge=1)
    status: str = "queued"


@router.post("")
def create_foundation_job(body: FoundationJobRequest) -> dict:
    payload = body.model_dump()
    payload["schema_version"] = "ailovanta.foundation_job.v1"
    try:
        job = foundation_jobs.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "foundation_job": job}


@router.get("")
def list_foundation_jobs(limit: int = 50) -> dict:
    return {"foundation_jobs": foundation_jobs.list_jobs(limit=limit)}


@router.get("/{job_id}")
def get_foundation_job(job_id: str) -> dict:
    job = foundation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="foundation job not found")
    return {"foundation_job": job}
