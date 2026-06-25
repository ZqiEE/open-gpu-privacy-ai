from __future__ import annotations

from pathlib import Path
from typing import Any

from api.ap import ok as check_ok
from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor
from api.route_book import RouteBook


def apply2(path: str | Path, runtime_id: str = "rt-owned-1", node_id: str = "node-owned-1", route_key: str = "owned-chat/default") -> dict[str, Any]:
    gate = check_ok(path)
    imported = import_foundation_result_file(path)
    binding = imported.get("artifact_binding") or {}
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    before = OwnedDoctor().check(model_key)
    action = None
    route = None
    if gate.get("ok"):
        action = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=runtime_id, node_id=node_id))
    after = OwnedDoctor().check(model_key)
    if gate.get("ok") and after.get("ok"):
        route = RouteBook().set_active(route_key, model_key, binding_id=binding.get("binding_id"), reason="gated_apply_ready", metadata={"runtime_id": runtime_id, "node_id": node_id})
    return {"ok": bool(gate.get("ok") and after.get("ok") and route), "gate": gate, "imported": imported, "before": before, "action": action, "after": after, "route": route}
