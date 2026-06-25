from __future__ import annotations

from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.owned_doctor import OwnedDoctor
from api.route_book import RouteBook


ACTIVE_BINDING_STATUSES = {"active", "candidate"}


class RouteHealth:
    def __init__(self, routes: RouteBook | None = None, bindings: ArtifactBindingStore | None = None, doctor: OwnedDoctor | None = None) -> None:
        self.routes = routes or RouteBook()
        self.bindings = bindings or ArtifactBindingStore()
        self.doctor = doctor or OwnedDoctor()

    def check(self, route_key: str = "owned-chat/default") -> dict[str, Any]:
        route = self.routes.get(route_key)
        blockers: list[str] = []
        if not route:
            return {"ok": False, "route_key": route_key, "route": None, "blockers": ["missing_route"]}
        if route.get("status") != "active":
            blockers.append("route_not_active")
        model_key = str(route.get("model_key") or "")
        if not model_key:
            blockers.append("missing_model_key")
        binding = self.bindings.latest_for_model(model_key) if model_key else None
        if not binding:
            blockers.append("missing_artifact_binding")
        elif binding.get("status") not in ACTIVE_BINDING_STATUSES:
            blockers.append("binding_not_active")
        runtime = self.doctor.check(model_key) if model_key else {"ok": False, "blockers": ["missing_model_key"]}
        if not runtime.get("ok"):
            blockers.extend(str(item) for item in runtime.get("blockers", []) or ["runtime_not_ready"])
        return {
            "ok": not blockers,
            "route_key": route_key,
            "route": route,
            "model_key": model_key,
            "binding": binding,
            "runtime": {"ok": runtime.get("ok"), "blockers": runtime.get("blockers")},
            "blockers": sorted(set(blockers)),
        }

    def disable_if_bad(self, route_key: str = "owned-chat/default", reason: str = "route_health_failed") -> dict[str, Any]:
        status = self.check(route_key)
        if status.get("ok"):
            return {"changed": False, "status": status}
        disabled = self.routes.disable(route_key, reason=reason + ":" + ",".join(status.get("blockers", []))) if status.get("route") else None
        return {"changed": bool(disabled), "status": status, "disabled": disabled}
