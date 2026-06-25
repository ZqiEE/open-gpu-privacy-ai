from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.receipt_flow import build_and_apply


def run_from_payload(payload: dict[str, Any], root: str | Path = "runtime_data/parcels/runs") -> dict[str, Any] | None:
    plan = payload.get("plan_path")
    if not payload.get("apply_flow") or not plan:
        return None
    run_id = "run_" + uuid4().hex[:12]
    result = build_and_apply(plan_path=plan, core_path=payload.get("core_path") or "../ailovanta-core", result_output=payload.get("result_output") or "runtime_data/parcels/foundation_result.json")
    record = {"run_id": run_id, "ok": bool(result.get("ok")), "submit_id": payload.get("id"), "result": result, "created_at": round(time(), 3)}
    path = Path(root) / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**record, "path": str(path)}


def list_runs(root: str | Path = "runtime_data/parcels/runs", limit: int = 20) -> list[dict[str, Any]]:
    paths = sorted(Path(root).glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]
