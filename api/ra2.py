from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from api.ap import ok as check_ok
from api.artifact_integrity import verify_artifact_uri
from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor
from api.route_book import RouteBook
from api.route_health import RouteHealth


def should_verify_artifact(value: bool | None) -> bool:
    if value is not None:
        return bool(value)
    return os.getenv("AILOVANTA_VERIFY_ROUTE_ARTIFACT", "false").lower() in {"1", "true", "yes", "on"}


def should_verify_distribution(value: bool | None) -> bool:
    if value is not None:
        return bool(value)
    return os.getenv("AILOVANTA_VERIFY_ROUTE_DISTRIBUTION", "false").lower() in {"1", "true", "yes", "on"}


def should_verify_chain(value: bool | None) -> bool:
    if value is not None:
        return bool(value)
    return os.getenv("AILOVANTA_VERIFY_ROUTE_CHAIN", "false").lower() in {"1", "true", "yes", "on"}


def check_binding_artifact(binding: dict[str, Any], enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"ok": True, "skipped": True, "reason": "disabled"}
    uri = str(binding.get("checkpoint_uri") or binding.get("backend_ref") or "")
    expected = str(binding.get("artifact_hash") or "")
    return verify_artifact_uri(uri, expected)


def apply2(
    path: str | Path,
    runtime_id: str = "rt-owned-1",
    node_id: str = "node-owned-1",
    route_key: str = "owned-chat/default",
    verify_artifact: bool | None = None,
    verify_distribution: bool | None = None,
    verify_chain: bool | None = None,
) -> dict[str, Any]:
    gate = check_ok(path)
    imported = import_foundation_result_file(path)
    binding = imported.get("artifact_binding") or {}
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    verify_enabled = should_verify_artifact(verify_artifact)
    distribution_enabled = should_verify_distribution(verify_distribution)
    chain_enabled = should_verify_chain(verify_chain)
    artifact_integrity = check_binding_artifact(binding, verify_enabled) if binding else {"ok": False, "reason": "missing_binding"}
    route_health = RouteHealth()
    artifact_distribution = route_health.check_artifact_distribution(binding) if binding and distribution_enabled else {"ok": True, "skipped": True, "reason": "disabled"}
    chain_anchor = route_health.check_chain_anchor(binding) if binding and chain_enabled else {"ok": True, "skipped": True, "reason": "disabled"}
    before = OwnedDoctor().check(model_key)
    action = None
    route = None
    artifact_ok = bool(artifact_integrity.get("ok"))
    distribution_ok = bool(artifact_distribution.get("ok"))
    chain_ok = bool(chain_anchor.get("ok"))
    if gate.get("ok") and artifact_ok and distribution_ok and chain_ok:
        action = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=runtime_id, node_id=node_id))
    after = OwnedDoctor().check(model_key)
    if gate.get("ok") and artifact_ok and distribution_ok and chain_ok and after.get("ok"):
        route = RouteBook().set_active(route_key, model_key, binding_id=binding.get("binding_id"), reason="gated_apply_ready", metadata={"runtime_id": runtime_id, "node_id": node_id, "artifact_integrity": artifact_integrity, "artifact_distribution": artifact_distribution, "chain_anchor": chain_anchor})
    return {"ok": bool(gate.get("ok") and artifact_ok and distribution_ok and chain_ok and after.get("ok") and route), "gate": gate, "imported": imported, "artifact_integrity": artifact_integrity, "artifact_distribution": artifact_distribution, "chain_anchor": chain_anchor, "before": before, "action": action, "after": after, "route": route}
