from __future__ import annotations

from typing import Any

from api.backup_store import BackupStore
from api.prod_ready_plus import check_abuse_controls, check_production_ready_plus
from api.route_health import RouteHealth
from api.runtime_readiness import RuntimeReadiness
from api.runtime_store import RuntimeStore
from api.security_review import run_security_review


def severity_for(blocker: str) -> str:
    if blocker.startswith(("backup:", "runtime_route:", "route:", "artifact_store_error", "anchor_adapter_error", "review:")):
        return "critical"
    if blocker.startswith(("abuse:", "readiness:", "missing_")):
        return "high"
    return "warning"


def make_alert(source: str, message: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"source": source, "severity": severity_for(message), "message": message, "metadata": metadata or {}}


class AlertSummary:
    def __init__(self) -> None:
        self.runtime = RuntimeStore()

    def collect(self, route_key: str = "owned-chat/default", verify_bytes: bool = False) -> dict[str, Any]:
        alerts: list[dict[str, Any]] = []
        prod = check_production_ready_plus(route_key=route_key, verify_bytes=verify_bytes)
        for blocker in prod.get("blockers", []):
            alerts.append(make_alert("prod_ready_plus", str(blocker)))
        route = RouteHealth().check(route_key, verify_artifact=verify_bytes)
        for blocker in route.get("blockers", []):
            alerts.append(make_alert("route_health", str(blocker), {"route_key": route_key}))
        runtime_route = RuntimeReadiness().check_route(route_key)
        if not runtime_route.get("ok"):
            alerts.append(make_alert("runtime_route", str(runtime_route.get("reason")), {"route_key": route_key}))
        backup = BackupStore().latest_status()
        if not backup.get("ok"):
            alerts.append(make_alert("backup", str(backup.get("reason") or "backup_not_ready")))
        abuse = check_abuse_controls()
        for blocker in abuse.get("blockers", []):
            alerts.append(make_alert("abuse_controls", str(blocker)))
        review = run_security_review()
        for blocker in review.get("blockers", []):
            alerts.append(make_alert("release_review", "review:" + str(blocker)))
        rt = self.runtime.status()
        if int(rt.get("runtimes", 0)) <= 0:
            alerts.append(make_alert("runtime", "no_runtime_nodes"))
        if int(rt.get("models", 0)) <= 0:
            alerts.append(make_alert("runtime", "no_runtime_models"))
        levels: dict[str, int] = {}
        for alert in alerts:
            levels[alert["severity"]] = levels.get(alert["severity"], 0) + 1
        ok = not any(alert["severity"] in {"critical", "high"} for alert in alerts)
        return {"ok": ok, "route_key": route_key, "verify_bytes": verify_bytes, "levels": levels, "alerts": alerts, "prod_ready_plus": prod, "route_health": route, "runtime_route": runtime_route, "backup": backup, "runtime": rt, "abuse_controls": abuse, "release_review": review}
