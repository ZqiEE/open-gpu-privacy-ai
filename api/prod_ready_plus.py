from __future__ import annotations

from pathlib import Path
from typing import Any

from api.prod_ready import check_production_ready
from api.runtime_readiness import RuntimeReadiness


def check_production_ready_plus(result_path: str | Path | None = None, route_key: str = "owned-chat/default", verify_bytes: bool = False) -> dict[str, Any]:
    base = check_production_ready(result_path=result_path, route_key=route_key, verify_bytes=verify_bytes)
    runtime_route = RuntimeReadiness().check_route(route_key)
    blockers = list(base.get("blockers", []))
    if not runtime_route.get("ok"):
        blockers.append("runtime_route:" + str(runtime_route.get("reason")))
    return {**base, "ok": not blockers, "stage": "production_ready" if not blockers else "blocked", "blockers": sorted(set(blockers)), "runtime_route": runtime_route}
