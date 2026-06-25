from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.model_plan import build_model_plan, combine_results, jobs_for_plan
from api.storage import SchedulerStore

router = APIRouter(prefix="/swarm-model", tags=["swarm-model"])
store = SchedulerStore()
_swarm_plans: dict[str, dict[str, Any]] = {}
_swarm_deltas: dict[str, list[dict[str, Any]]] = {}


class SwarmPlanRequest(BaseModel):
    model_id: str = "ailovanta-foundation"
    base_model: str = "native"
    target_version: str = "v0.1"
    dataset_uri: str
    total_tokens: int = Field(gt=0)
    stage: Literal["build", "adapt", "score"] = "build"
    shard_tokens: int = Field(default=8192, gt=0)
    max_runtime_seconds: int = Field(default=600, gt=0)
    min_gpu_memory_gb: float = Field(default=8.0, ge=0)
    policy_mode: str = "open_research"
    enqueue: bool = True


class DeltaSubmitRequest(BaseModel):
    plan_id: str
    delta: dict[str, Any]


@router.post("/plans")
def create_swarm_plan(body: SwarmPlanRequest) -> dict[str, Any]:
    plan = build_model_plan(body.model_id, body.target_version, body.dataset_uri, body.total_tokens, body.shard_tokens, body.min_gpu_memory_gb, body.stage)
    plan_dict = plan.to_dict()
    _swarm_plans[plan.plan_id] = plan_dict
    jobs = jobs_for_plan(plan)
    enqueued: list[dict[str, Any]] = []
    if body.enqueue:
        for job in jobs:
            enqueued.append(store.enqueue_job(job["job_id"], job["job_type"], job["payload"]))
    return {"ok": True, "plan": plan_dict, "job_count": len(jobs), "enqueued": enqueued}


@router.get("/plans")
def list_swarm_plans() -> dict[str, Any]:
    return {"plans": list(_swarm_plans.values())}


@router.get("/plans/{plan_id}")
def get_swarm_plan(plan_id: str) -> dict[str, Any]:
    return {"plan": _swarm_plans.get(plan_id), "deltas": _swarm_deltas.get(plan_id, [])}


@router.post("/deltas")
def submit_delta(body: DeltaSubmitRequest) -> dict[str, Any]:
    _swarm_deltas.setdefault(body.plan_id, []).append(body.delta)
    return {"ok": True, "plan_id": body.plan_id, "delta_count": len(_swarm_deltas[body.plan_id])}


@router.post("/plans/{plan_id}/aggregate")
def aggregate_plan(plan_id: str) -> dict[str, Any]:
    plan = _swarm_plans.get(plan_id)
    if not plan:
        return {"ok": False, "error": "plan not found"}
    checkpoint_set = combine_results(plan, _swarm_deltas.get(plan_id, []))
    return {"ok": True, "checkpoint_set": checkpoint_set}
