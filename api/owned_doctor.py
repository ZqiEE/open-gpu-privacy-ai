from __future__ import annotations

from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.runtime_ref import check_runtime_ref
from api.runtime_store import RuntimeStore


class OwnedDoctor:
    def __init__(self, bindings: ArtifactBindingStore | None = None, runtime: RuntimeStore | None = None) -> None:
        self.bindings = bindings or ArtifactBindingStore()
        self.runtime = runtime or RuntimeStore()

    def check(self, model_key: str = "ailovanta-owned:candidate") -> dict[str, Any]:
        binding = self.bindings.latest_for_model(model_key, active_only=True)
        binding_ok = binding is not None
        ref_report = check_runtime_ref(binding) if binding else {"ready": False, "reason": "missing_binding"}
        model = self.runtime.get_model(model_key)
        nodes = self.runtime.list_runtimes()
        warm_nodes = [node for node in nodes if model_key in node.get("cached_models", []) and node.get("status") == "online"]
        model_ok = bool(model and model.get("status") == "active")
        node_ok = bool(warm_nodes)
        ref_ok = bool(ref_report.get("ready"))
        blockers = []
        if not binding_ok:
            blockers.append("missing_artifact_binding")
        if binding_ok and not ref_ok:
            blockers.append("backend_ref_not_ready")
        if not model_ok:
            blockers.append("runtime_model_not_active")
        if not node_ok:
            blockers.append("no_online_node_with_cached_model")
        return {
            "ok": not blockers,
            "model_key": model_key,
            "blockers": blockers,
            "binding": binding,
            "ref_check": ref_report,
            "runtime_model": model,
            "warm_nodes": warm_nodes,
            "runtime_nodes_count": len(nodes),
        }
