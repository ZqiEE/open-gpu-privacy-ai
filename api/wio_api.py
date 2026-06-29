from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.parcel_store import ParcelStore
from api.wio import task_envelope, verify_result, verify_task_envelope

router = APIRouter(prefix="/wio", tags=["wio"])
store = ParcelStore()


class TaskBody(BaseModel):
    plan: dict[str, Any]
    node_id: str
    input_uri: str
    output_uri: str


class ResultBody(BaseModel):
    payload: dict[str, Any]
    require_valid: bool = True


@router.post("/task")
def create_task(body: TaskBody) -> dict[str, Any]:
    item = task_envelope(body.plan, body.node_id, body.input_uri, body.output_uri)
    store.put_many("worker_tasks", [item])
    return {"ok": True, "item": item}


@router.get("/tasks")
def list_tasks(node_id: str | None = None, status: str | None = "open") -> dict[str, Any]:
    return {"tasks": store.list_inbox(node_id=node_id, status=status)}


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    item = store.get_inbox(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="task not found")
    return {"task": item}


@router.post("/tasks/{task_id}/claim")
def claim_task(task_id: str, node_id: str) -> dict[str, Any]:
    item = store.get_inbox(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="task not found")
    task_check = verify_task_envelope(item)
    if not task_check.get("ok"):
        raise HTTPException(status_code=400, detail=task_check)
    task_node = item.get("node_id") or item.get("task", {}).get("node_id")
    if task_node and task_node != node_id:
        raise HTTPException(status_code=403, detail="task belongs to another node")
    updated = store.update_inbox(task_id, {"status": "claimed", "claimed_by": node_id})
    return {"ok": True, "task": updated, "task_check": task_check}


@router.post("/result")
def submit_result(body: ResultBody) -> dict[str, Any]:
    task_id = body.payload.get("task_id")
    task_item = store.get_inbox(str(task_id)) if task_id else None
    checked = verify_result(body.payload, task_item)
    if body.require_valid and not checked.get("ok"):
        raise HTTPException(status_code=400, detail=checked)
    item = store.put_outbox(body.payload)
    if task_id:
        store.update_inbox(str(task_id), {"status": "done", "result_id": item.get("id")})
    return {"ok": True, "checked": checked, "item": item}


@router.get("/results")
def list_results() -> dict[str, Any]:
    return {"results": store.list_outbox()}
