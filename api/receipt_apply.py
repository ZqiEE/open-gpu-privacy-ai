from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from api.artifact_integrity import verify_artifact_uri
from api.foundation_result_import import import_foundation_result_file
from api.model_warm import ModelWarm, WarmSpec
from api.owned_doctor import OwnedDoctor
from api.ra2 import should_verify_chain, should_verify_distribution
from api.route_health import RouteHealth


def should_verify(value: bool | None) -> bool:
    if value is not None:
        return bool(value)
    return os.getenv("AILOVANTA_VERIFY_ROUTE_ARTIFACT", "false").lower() in {"1", "true", "yes", "on"}


def apply_result(path: str | Path, runtime_id: str = "rt-owned-1", node_id: str = "node-owned-1", verify_artifact: bool | None = None, verify_distribution: bool | None = None, verify_chain: bool | None = None) -> dict[str, Any]:
    imported = import_foundation_result_file(path)
    binding = imported.get("artifact_binding") or {}
    model_key = binding.get("model_key") or "ailovanta-owned:candidate"
    verify_enabled = should_verify(verify_artifact)
    distribution_enabled = should_verify_distribution(verify_distribution)
    chain_enabled = should_verify_chain(verify_chain)
    artifact_integrity = {"ok": True, "skipped": True, "reason": "disabled"}
    if verify_enabled:
        artifact_integrity = verify_artifact_uri(str(binding.get("checkpoint_uri") or binding.get("backend_ref") or ""), str(binding.get("artifact_hash") or ""))
    route_health = RouteHealth()
    artifact_distribution = route_health.check_artifact_distribution(binding) if binding and distribution_enabled else {"ok": True, "skipped": True, "reason": "disabled"}
    chain_anchor = route_health.check_chain_anchor(binding) if binding and chain_enabled else {"ok": True, "skipped": True, "reason": "disabled"}
    before = OwnedDoctor().check(model_key)
    action = None
    if artifact_integrity.get("ok") and artifact_distribution.get("ok") and chain_anchor.get("ok"):
        action = ModelWarm().run(WarmSpec(model_key=model_key, runtime_id=runtime_id, node_id=node_id))
    after = OwnedDoctor().check(model_key)
    return {"ok": bool(artifact_integrity.get("ok") and artifact_distribution.get("ok") and chain_anchor.get("ok") and after.get("ok")), "imported": imported, "artifact_integrity": artifact_integrity, "artifact_distribution": artifact_distribution, "chain_anchor": chain_anchor, "before": before, "action": action, "after": after}
