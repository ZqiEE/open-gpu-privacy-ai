from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.replica_repair import ReplicaRepairStore

router = APIRouter(prefix="/replicas/repair", tags=["replica-repair"])


class PlanRepairsBody(BaseModel):
    artifact_hash: str | None = None
    target_nodes: list[str] = Field(default_factory=list)
    max_tasks: int | None = Field(default=None, ge=1)


class AssignRepairBody(BaseModel):
    node_id: str


class CompleteRepairBody(BaseModel):
    node_id: str | None = None
    location: str | None = None


@router.post("/plan")
def plan_replica_repairs(body: PlanRepairsBody) -> dict[str, Any]:
    return ReplicaRepairStore().plan_repairs(artifact_hash=body.artifact_hash, target_nodes=body.target_nodes or None, max_tasks=body.max_tasks)


@router.get("/tasks")
def list_replica_repair_tasks(status: str | None = None, limit: int = 100) -> dict[str, Any]:
    return {"tasks": ReplicaRepairStore().list_tasks(status=status, limit=limit)}


@router.post("/tasks/{task_id}/assign")
def assign_replica_repair_task(task_id: str, body: AssignRepairBody) -> dict[str, Any]:
    try:
        return {"task": ReplicaRepairStore().assign(task_id, body.node_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404 if "not found" in str(exc) else 400, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/complete")
def complete_replica_repair_task(task_id: str, body: CompleteRepairBody) -> dict[str, Any]:
    try:
        return ReplicaRepairStore().complete(task_id, node_id=body.node_id, location=body.location)
    except ValueError as exc:
        raise HTTPException(status_code=404 if "not found" in str(exc) else 400, detail=str(exc)) from exc
