from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.model_monitor import ModelMonitorStore

router = APIRouter(prefix="/model-monitor", tags=["model-monitor"])
store = ModelMonitorStore()


class ShadowRequest(BaseModel):
    candidate_model: str
    baseline_model: str
    artifact_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromoteRequest(BaseModel):
    shadow_id: str


class MetricRequest(BaseModel):
    model: str
    metrics: dict[str, float]
    mode: str = "shadow"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RollbackCheckRequest(BaseModel):
    live_model: str
    baseline_metrics: dict[str, float]
    max_drop: float = 0.05


@router.post("/shadow")
def register_shadow(body: ShadowRequest) -> dict:
    return {"ok": True, "shadow": store.register_shadow(body.candidate_model, body.baseline_model, body.artifact_hash, body.metadata)}


@router.post("/promote")
def promote_live(body: PromoteRequest) -> dict:
    try:
        return {"ok": True, "live": store.promote_live(body.shadow_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/metrics")
def record_metric(body: MetricRequest) -> dict:
    return {"ok": True, "metric": store.record_metric(body.model, body.metrics, body.mode, body.metadata)}


@router.post("/rollback-check")
def rollback_check(body: RollbackCheckRequest) -> dict:
    return {"ok": True, "action": store.evaluate_rollback(body.live_model, body.baseline_metrics, body.max_drop)}


@router.get("/shadow")
def list_shadow() -> dict:
    return {"items": store.list_shadows()}


@router.get("/live")
def list_live() -> dict:
    return {"items": store.list_live()}


@router.get("/actions")
def list_actions() -> dict:
    return {"items": store.list_actions()}
