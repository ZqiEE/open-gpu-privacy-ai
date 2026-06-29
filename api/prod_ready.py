from __future__ import annotations

from pathlib import Path
from typing import Any

from api.anchor_adapter import get_anchor_adapter
from api.artifact_store import get_artifact_store
from api.prod_config import load_config, redacted_env
from api.readiness_audit import ReadinessAudit
from api.route_health import RouteHealth


def check_production_ready(result_path: str | Path | None = None, route_key: str = "owned-chat/default", verify_bytes: bool = False, verify_distribution: bool = False, verify_chain: bool = False) -> dict[str, Any]:
    cfg = load_config()
    blockers: list[str] = []
    warnings: list[str] = []

    if cfg.env == "local":
        warnings.append("env_is_local")
    if not cfg.public_base_url and cfg.env != "local":
        blockers.append("missing_public_base_url")
    if cfg.worker_mode == "local" and cfg.env != "local":
        blockers.append("worker_mode_local_in_production")
    if cfg.model_backend == "local" and cfg.env != "local":
        blockers.append("model_backend_local_in_production")

    route = RouteHealth().check(route_key, verify_artifact=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
    if not route.get("ok"):
        blockers.extend("route:" + str(item) for item in route.get("blockers", []))

    artifact_store_ok = True
    anchor_ok = True
    try:
        get_artifact_store()
    except Exception as exc:
        artifact_store_ok = False
        blockers.append("artifact_store_error:" + exc.__class__.__name__)
    try:
        get_anchor_adapter()
    except Exception as exc:
        anchor_ok = False
        blockers.append("anchor_adapter_error:" + exc.__class__.__name__)

    readiness = ReadinessAudit().production_check(verify_bytes=verify_bytes)
    if not readiness.get("ok"):
        blockers.extend("readiness:" + str(item) for item in readiness.get("blockers", []))
    warnings.extend("readiness:" + str(item) for item in readiness.get("warnings", []))

    result_exists = None
    if result_path is not None:
        result_exists = Path(result_path).exists()
        if not result_exists:
            blockers.append("missing_result_file")

    return {
        "ok": not blockers,
        "stage": "production_ready" if not blockers else "blocked",
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "verify_bytes": verify_bytes,
        "verify_distribution": verify_distribution,
        "verify_chain": verify_chain,
        "config": cfg.to_dict(),
        "env": redacted_env(),
        "route_health": route,
        "readiness": readiness,
        "artifact_store_ok": artifact_store_ok,
        "anchor_adapter_ok": anchor_ok,
        "result_exists": result_exists,
    }
