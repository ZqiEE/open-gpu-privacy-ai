from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.ckpt_merge import merge_ckpts
from api.ckpt_run import newest_ref, run_ckpt

router = APIRouter(prefix="/ck", tags=["ck"])
BUILT: dict[str, dict[str, Any]] = {}


class Body(BaseModel):
    text: str
    ref: str | None = None
    max_new: int = 80


class BuildBody(BaseModel):
    plan_id: str
    model_id: str = "ailovanta-foundation"
    version: str = "v0.1"
    stage: str = "build"
    items: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/build")
def build(body: BuildBody) -> dict:
    plan = {"plan_id": body.plan_id, "model_id": body.model_id, "version": body.version, "stage": body.stage}
    try:
        result = merge_ckpts(plan, body.items)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    BUILT[body.plan_id] = result
    return {"ok": True, "checkpoint": result}


@router.post("/run")
def run(body: Body) -> dict:
    ref = body.ref or newest_ref()
    if not ref:
        return {"ok": False, "error": "no checkpoint found"}
    try:
        result = run_ckpt(body.text, ref, body.max_new)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "checkpoint_ref": ref}
    return {"ok": True, **result}
