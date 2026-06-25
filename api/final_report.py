from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.ap import ok as apply_gate
from api.g2 import eval_payload
from api.owned_doctor import OwnedDoctor


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def report(result_path: str | Path, model_key: str = "ailovanta-owned:candidate") -> dict[str, Any]:
    result = load(result_path)
    artifact = result.get("artifact") if isinstance(result.get("artifact"), dict) else {}
    gate = apply_gate(result_path)
    runtime = OwnedDoctor().check(model_key)
    payload = eval_payload(result)
    return {
        "ok": bool(gate.get("ok") and runtime.get("ok")),
        "artifact_id": artifact.get("artifact_id"),
        "artifact_hash": artifact.get("artifact_hash"),
        "model_key": model_key,
        "apply_gate": gate,
        "runtime": {"ok": runtime.get("ok"), "blockers": runtime.get("blockers")},
        "eval_guardrails": payload.get("guardrails"),
    }
