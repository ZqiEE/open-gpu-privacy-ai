from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from api.backup_store import BackupStore
from api.owned_ready_probe import check_owned_chat_default
from api.prod_ready import check_production_ready
from api.runtime_readiness import RuntimeReadiness
from api.security_review import run_security_review


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


def check_backup_controls() -> dict[str, Any]:
    status = BackupStore().latest_status()
    if not status.get("ok"):
        return {"ok": False, "blockers": [str(status.get("reason") or "backup_not_ready")], "status": status}
    return {"ok": True, "blockers": [], "status": status}


def check_production_ready_plus(result_path: str | Path | None = None, route_key: str = "owned-chat/default", verify_bytes: bool = False) -> dict[str, Any]:
    base = check_production_ready(result_path=result_path, route_key=route_key, verify_bytes=verify_bytes)
    runtime_route = RuntimeReadiness().check_route(route_key)
    default_chat = check_owned_chat_default(route_key)
    abuse = check_abuse_controls()
    backups = check_backup_controls()
    review = run_security_review()
    blockers = list(base.get("blockers", []))
    warnings = list(base.get("warnings", []))
    if not runtime_route.get("ok"):
        blockers.append("runtime_route:" + str(runtime_route.get("reason")))
    if not default_chat.get("owned_model_ready"):
        blockers.append("owned_chat_default:not_ready")
    if not abuse.get("ok"):
        blockers.extend("abuse:" + str(item) for item in abuse.get("blockers", []))
    if not backups.get("ok"):
        blockers.extend("backup:" + str(item) for item in backups.get("blockers", []))
    if not review.get("ok"):
        blockers.extend("review:" + str(item) for item in review.get("blockers", []))
    warnings.extend("abuse:" + str(item) for item in abuse.get("warnings", []))
    warnings.extend("review:" + str(item) for item in review.get("warnings", []))
    return {**base, "ok": not blockers, "stage": "production_ready" if not blockers else "blocked", "blockers": sorted(set(blockers)), "warnings": sorted(set(warnings)), "runtime_route": runtime_route, "owned_chat_default": default_chat, "abuse_controls": abuse, "backup_controls": backups, "release_review": review}
