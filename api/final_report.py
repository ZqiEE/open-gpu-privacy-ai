from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.ap import ok as apply_gate
from api.g2 import eval_payload
from api.owned_doctor import OwnedDoctor
from api.route_book import RouteBook


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def final_blockers(gate: dict[str, Any], runtime: dict[str, Any], artifact: dict[str, Any], route: dict[str, Any] | None, model_key: str) -> list[str]:
    blockers: list[str] = []
    if not artifact.get("artifact_hash"):
        blockers.append("missing_artifact_hash")
    if not route:
        blockers.append("missing_active_route")
    elif route.get("model_key") != model_key:
        blockers.append("active_route_model_mismatch")
    blockers.extend(str(item) for item in gate.get("blockers", []) or [])
    blockers.extend(str(item) for item in runtime.get("blockers", []) or [])
    return sorted(set(blockers))


def report(result_path: str | Path, model_key: str = "ailovanta-owned:candidate", route_key: str = "owned-chat/default") -> dict[str, Any]:
    result = load(result_path)
    artifact = result.get("artifact") if isinstance(result.get("artifact"), dict) else {}
    gate = apply_gate(result_path)
    runtime = OwnedDoctor().check(model_key)
    route = RouteBook().active(route_key)
    payload = eval_payload(result)
    blockers = final_blockers(gate, runtime, artifact, route, model_key)
    return {
        "ok": not blockers,
        "stage": "runtime_ready" if not blockers else "blocked",
        "blockers": blockers,
        "artifact_id": artifact.get("artifact_id"),
        "artifact_hash": artifact.get("artifact_hash"),
        "model_key": model_key,
        "route_key": route_key,
        "active_route": route,
        "apply_gate": gate,
        "runtime": {"ok": runtime.get("ok"), "blockers": runtime.get("blockers")},
        "eval_guardrails": payload.get("guardrails"),
    }
