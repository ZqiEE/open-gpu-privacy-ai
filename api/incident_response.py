from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.alert_summary import AlertSummary
from api.backup_store import BackupStore
from api.route_book import RouteBook


DEFAULT_ROUTE_KEY = "owned-chat/default"
ACTION_DISABLE_ROUTE = "disable_route"
ACTION_OBSERVE = "observe"
ACTION_BACKUP_ONLY = "backup_only"


def actionable(alert: dict[str, Any]) -> bool:
    return alert.get("severity") in {"critical", "high"}


def route_related(alert: dict[str, Any]) -> bool:
    source = str(alert.get("source") or "")
    message = str(alert.get("message") or "")
    return source in {"route_health", "runtime_route", "prod_ready_plus"} or message.startswith(("route:", "runtime_route:"))


class IncidentResponse:
    def __init__(self, alerts: AlertSummary | None = None, backups: BackupStore | None = None, routes: RouteBook | None = None, log_root: str | Path = "runtime_data/incidents") -> None:
        self.alerts = alerts or AlertSummary()
        self.backups = backups or BackupStore()
        self.routes = routes or RouteBook()
        self.log_root = Path(log_root)
        self.log_root.mkdir(parents=True, exist_ok=True)

    def plan(self, route_key: str = DEFAULT_ROUTE_KEY, verify_bytes: bool = False, verify_distribution: bool = False, verify_chain: bool = False) -> dict[str, Any]:
        summary = self.alerts.collect(route_key=route_key, verify_bytes=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
        active_alerts = [item for item in summary.get("alerts", []) if actionable(item)]
        actions: list[dict[str, Any]] = []
        if not active_alerts:
            actions.append({"action": ACTION_OBSERVE, "reason": "no_high_or_critical_alerts"})
        else:
            actions.append({"action": "create_backup", "reason": "pre_incident_snapshot"})
            if any(route_related(item) for item in active_alerts):
                actions.append({"action": ACTION_DISABLE_ROUTE, "route_key": route_key, "reason": "route_related_alert"})
            else:
                actions.append({"action": ACTION_BACKUP_ONLY, "reason": "non_route_alerts"})
        return {"ok": not active_alerts, "route_key": route_key, "verify_bytes": verify_bytes, "verify_distribution": verify_distribution, "verify_chain": verify_chain, "alerts": active_alerts, "actions": actions, "summary": summary}

    def execute(self, route_key: str = DEFAULT_ROUTE_KEY, verify_bytes: bool = False, verify_distribution: bool = False, verify_chain: bool = False, dry_run: bool = True) -> dict[str, Any]:
        plan = self.plan(route_key=route_key, verify_bytes=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
        incident_id = "incident_" + uuid4().hex[:12]
        results: list[dict[str, Any]] = []
        for action in plan.get("actions", []):
            kind = action.get("action")
            if kind == "create_backup":
                if dry_run:
                    results.append({"action": kind, "dry_run": True, "would_create_backup": True})
                else:
                    results.append({"action": kind, "backup": self.backups.create(label=incident_id)})
            elif kind == ACTION_DISABLE_ROUTE:
                if dry_run:
                    results.append({"action": kind, "dry_run": True, "route_key": route_key, "would_disable": True})
                else:
                    results.append({"action": kind, "route": self.routes.disable(route_key, reason="incident:" + incident_id)})
            else:
                results.append({"action": kind, "dry_run": dry_run, "reason": action.get("reason")})
        payload = {"ok": plan.get("ok") or dry_run, "incident_id": incident_id, "dry_run": dry_run, "created_at": round(time(), 3), "plan": plan, "results": results}
        return self._log(payload)

    def list_logs(self) -> list[dict[str, Any]]:
        items = []
        for path in sorted(self.log_root.glob("*.json"), reverse=True):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                items.append({"log_id": path.stem, "ok": False, "reason": "incident_log_read_error"})
        return items

    def _log(self, payload: dict[str, Any]) -> dict[str, Any]:
        path = self.log_root / f"{payload['incident_id']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
