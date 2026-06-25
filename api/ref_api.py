from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.artifact_binding import ArtifactBindingStore
from api.foundation_result_import import set_runtime_model_status
from api.runtime_ref import check_runtime_ref
from api.runtime_store import RuntimeStore

router = APIRouter(prefix="/refs", tags=["refs"])
store = ArtifactBindingStore()
runtime_store = RuntimeStore()


@router.post("/{binding_id}/refresh")
def refresh_ref(binding_id: str) -> dict:
    item = store.get(binding_id)
    if not item:
        raise HTTPException(status_code=404, detail="binding not found")
    report = check_runtime_ref(item)
    if report["ready"] and item.get("status") == "unavailable":
        item = store.set_status(binding_id, "candidate") or item
        update = set_runtime_model_status(runtime_store, item["model_key"], "candidate")
    elif not report["ready"] and item.get("status") in {"active", "candidate"}:
        item = store.set_status(binding_id, "unavailable") or item
        update = set_runtime_model_status(runtime_store, item["model_key"], "unavailable")
    else:
        update = {"model_key": item.get("model_key"), "changed": False}
    return {"binding": item, "report": report, "runtime_status_update": update}
