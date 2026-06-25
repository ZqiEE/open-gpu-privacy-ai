from __future__ import annotations

from typing import Any

from api.runtime_store import RuntimeStore


def set_model_status(runtime: RuntimeStore, model_key: str, status: str) -> dict[str, Any]:
    with runtime.connect() as conn:
        before = conn.execute("SELECT status FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
        conn.execute("UPDATE runtime_models SET status = ? WHERE model_key = ?", (status, model_key))
        after = conn.execute("SELECT status FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
    return {"model_key": model_key, "before": before[0] if before else None, "after": after[0] if after else None, "found": after is not None}


def sync_model_with_ref_check(runtime: RuntimeStore, model_key: str, ready: bool) -> dict[str, Any]:
    current = runtime.get_model(model_key)
    if not current:
        return {"model_key": model_key, "found": False, "changed": False}
    if ready and current.get("status") == "unavailable":
        update = set_model_status(runtime, model_key, "candidate")
        return {**update, "changed": True}
    if not ready and current.get("status") in {"active", "candidate"}:
        update = set_model_status(runtime, model_key, "unavailable")
        return {**update, "changed": True}
    return {"model_key": model_key, "found": True, "before": current.get("status"), "after": current.get("status"), "changed": False}
