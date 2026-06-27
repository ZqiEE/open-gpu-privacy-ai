from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from api.prod_ready import check_production_ready
from api.runtime_readiness import RuntimeReadiness


def enabled(name: str) -> bool:
    return os.getenv(name, "false").lower() in {"1", "true", "yes", "on"}


def check_abuse_controls() -> dict[str, Any]:
    rate_limit_enabled = enabled("AILOVANTA_RATE_LIMIT_ENABLED")
    admin_token_set = bool(os.getenv("AILOVANTA_ADMIN_TOKEN"))
    blockers: list[str] = []
    warnings: list[str] = []
    if not rate_limit_enabled:
        blockers.append("rate_limit_disabled")
    if not admin_token_set:
        warnings.append("admin_token_missing")
    try:
        per_minute = int(os.getenv("AILOVANTA_RATE_LIMIT_PER_MINUTE", "120"))
    except ValueError:
        per_minute = 0
    if per_minute <= 0:
        blockers.append("bad_rate_limit_value")
    return {"ok": not blockers, "blockers": blockers, "warnings": warnings, "rate_limit_enabled": rate_limit_enabled, "rate_limit_per_minute": per_minute, "admin_token_set": admin_token_set}


def check_production_ready_plus(result_path: str | Path | None = None, route_key: str = "owned-chat/default", verify_bytes: bool = False) -> dict[str, Any]:
    base = check_production_ready(result_path=result_path, route_key=route_key, verify_bytes=verify_bytes)
    runtime_route = RuntimeReadiness().check_route(route_key)
    abuse = check_abuse_controls()
    blockers = list(base.get("blockers", []))
    warnings = list(base.get("warnings", []))
    if not runtime_route.get("ok"):
        blockers.append("runtime_route:" + str(runtime_route.get("reason")))
    if not abuse.get("ok"):
        blockers.extend("abuse:" + str(item) for item in abuse.get("blockers", []))
    warnings.extend("abuse:" + str(item) for item in abuse.get("warnings", []))
    return {**base, "ok": not blockers, "stage": "production_ready" if not blockers else "blocked", "blockers": sorted(set(blockers)), "warnings": sorted(set(warnings)), "runtime_route": runtime_route, "abuse_controls": abuse}
