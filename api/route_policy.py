from __future__ import annotations

from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.runtime_ref import check_runtime_ref


def check_route(model_id: str, model_key: str, request_id: str, bindings: ArtifactBindingStore | None = None) -> dict[str, Any] | None:
    if model_id != "ailovanta-owned":
        return None
    store = bindings or ArtifactBindingStore()
    item = store.latest_for_model_statuses(model_key, ("active",))
    if not item:
        return {"assigned": False, "reason": "no usable model binding", "request_id": request_id, "model_key": model_key}
    report = check_runtime_ref(item)
    if not report.get("ready"):
        return {"assigned": False, "reason": "model binding ref failed: " + str(report.get("reason")), "request_id": request_id, "model_key": model_key, "binding_id": item.get("binding_id")}
    return None
