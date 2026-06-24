from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.core_result_store import CoreResultStore
from api.runtime_store import RuntimeStore

router = APIRouter(prefix="/core/results", tags=["core-results"])
core_results = CoreResultStore()
runtime_store = RuntimeStore()


class CoreResultRequest(BaseModel):
    schema_version: str = "ailovanta.core_result.v1"
    source_job_id: str
    round_id: str
    accepted_candidates: int = Field(ge=0)
    next_model_version: str
    base_model: str = ""
    dataset_uri: str = ""
    summary_path: str = ""
    result_path: str = ""
    promotion_status: Literal["candidate", "promoted", "rejected"] = "candidate"


class RuntimeRegistrationRequest(BaseModel):
    model_id: str = "ailovanta-owned"
    privacy_level: Literal["public", "protected", "private"] = "protected"
    min_gpu_memory_gb: float = Field(default=8.0, ge=0)


@router.post("")
def register_core_result(body: CoreResultRequest) -> dict:
    try:
        result = core_results.register_manifest(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "core_result": result}


@router.get("")
def list_core_results(limit: int = 50) -> dict:
    return {"core_results": core_results.list_results(limit=limit)}


@router.post("/{result_id}/runtime")
def register_runtime_model_from_core_result(result_id: str, body: RuntimeRegistrationRequest) -> dict:
    try:
        return core_results.promote_to_runtime(
            result_id=result_id,
            runtime_store=runtime_store,
            model_id=body.model_id,
            privacy_level=body.privacy_level,
            min_gpu_memory_gb=body.min_gpu_memory_gb,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
