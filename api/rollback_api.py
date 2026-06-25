from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.rollback_executor import RollbackExecutor

router = APIRouter(prefix="/rollback", tags=["rollback"])
executor = RollbackExecutor()


class ActionRequest(BaseModel):
    action: dict[str, Any] = Field(default_factory=dict)


@router.post("/latest")
def execute_latest() -> dict:
    return {"ok": True, "result": executor.execute_latest()}


@router.post("/action")
def execute_action(body: ActionRequest) -> dict:
    return {"ok": True, "result": executor.execute_action(body.action)}


@router.get("/logs")
def list_logs() -> dict:
    return {"items": executor.list_logs()}
