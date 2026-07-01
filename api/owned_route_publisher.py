from __future__ import annotations

from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.model_warm import ModelWarm, WarmSpec
from api.route_book import RouteBook


DEFAULT_ROUTE_KEY = "owned-chat/default"


def publish_owned_route_if_active(
    binding: dict[str, Any],
    *,
    route_key: str = DEFAULT_ROUTE_KEY,
    routes: RouteBook | None = None,
    bindings: ArtifactBindingStore | None = None,
    warmer: ModelWarm | None = None,
    runtime_id: str = "rt-owned-1",
    node_id: str = "node-owned-1",
) -> dict[str, Any]:
    if not binding:
        return {"ok": False, "reason": "missing_binding", "route": None}
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    gate = metadata.get("promotion_gate") if isinstance(metadata.get("promotion_gate"), dict) else {}
    if binding.get("status") != "active":
        return {"ok": False, "reason": "binding_not_active", "binding_id": binding.get("binding_id"), "route": None}
    if gate and gate.get("ok") is not True:
        return {"ok": False, "reason": "promotion_gate_not_ok", "binding_id": binding.get("binding_id"), "gate": gate, "route": None}

    binding_store = bindings or ArtifactBindingStore()
    warm = warmer or ModelWarm(bindings=binding_store)
    warm_result = warm.run(WarmSpec(model_key=str(binding.get("model_key") or ""), runtime_id=runtime_id, node_id=node_id))
    if not warm_result.get("ok"):
        return {"ok": False, "reason": "runtime_warm_failed", "binding_id": binding.get("binding_id"), "warm": warm_result, "route": None}

    route = (routes or RouteBook()).set_active(
        route_key,
        str(binding["model_key"]),
        binding_id=str(binding.get("binding_id") or ""),
        reason="training_artifact_promotion_gate_passed",
        metadata={
            "runtime_id": runtime_id,
            "node_id": node_id,
            "artifact_hash": binding.get("artifact_hash"),
            "backend_kind": binding.get("backend_kind"),
            "promotion_gate": _compact_gate(gate),
            "training_worker_receipt": _compact_receipt(metadata.get("training_worker_receipt") if isinstance(metadata.get("training_worker_receipt"), dict) else {}),
        },
    )
    return {"ok": True, "reason": "published", "binding_id": binding.get("binding_id"), "warm": warm_result, "route": route}


def _compact_gate(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": gate.get("ok"),
        "decision": gate.get("decision"),
        "blockers": gate.get("blockers", []),
    }


def _compact_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_id": receipt.get("receipt_id"),
        "receipt_hash": receipt.get("receipt_hash"),
        "node_id": receipt.get("node_id"),
        "job_id": receipt.get("job_id"),
        "passed": receipt.get("passed"),
    }
