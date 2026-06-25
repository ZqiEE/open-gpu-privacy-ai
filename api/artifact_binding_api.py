from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore
from api.foundation_result_import import set_runtime_model_status
from api.runtime_ref import check_runtime_ref
from api.runtime_store import RuntimeStore

router = APIRouter(prefix="/artifact-bindings", tags=["artifact-bindings"])
store = ArtifactBindingStore()
runtime_store = RuntimeStore()


class StatusRequest(BaseModel):
    status: str


@router.get("")
def list_bindings(limit: int = 100) -> dict:
    return {"items": store.list_bindings(limit=limit)}


@router.get("/by-model/{model_key:path}")
def latest_for_model(model_key: str) -> dict:
    return {"binding": store.latest_for_model(model_key)}


@router.get("/{binding_id}")
def get_binding(binding_id: str) -> dict:
    item = store.get(binding_id)
    if not item:
        raise HTTPException(status_code=404, detail="binding not found")
    return {"binding": item}


@router.post("/{binding_id}/status")
def set_status(binding_id: str, body: StatusRequest) -> dict:
    item = store.set_status(binding_id, body.status)
    if not item:
        raise HTTPException(status_code=404, detail="binding not found")
    return {"binding": item}


@router.post("/{binding_id}/check")
def check_binding(binding_id: str) -> dict:
    item = store.get(binding_id)
    if not item:
        raise HTTPException(status_code=404, detail="binding not found")
    check = check_runtime_ref(item)
    update = {"model_key": item.get("model_key"), "changed": False}
    if check["ready"] and item.get("status") == "unavailable":
        item = store.set_status(binding_id, "candidate") or item
        update = set_runtime_model_status(runtime_store, item["model_key"], "candidate")
    if not check["ready"] and item.get("status") in {"active", "candidate"}:
        item = store.set_status(binding_id, "unavailable") or item
        update = set_runtime_model_status(runtime_store, item["model_key"], "unavailable")
    return {"binding": item, "check": check, "runtime_status_update": update}
