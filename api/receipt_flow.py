from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from api.parcel_receipts import export_receipts
from api.receipt_apply import apply_result


def run_json(command: list[str], cwd: Path | None = None) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def build_result(
    plan_path: str | Path,
    core_path: str | Path = "../ailovanta-core",
    receipts_output: str | Path = "runtime_data/parcels/checkpoint_receipts.json",
    set_output: str | Path = "runtime_data/parcels/checkpoint_set.json",
    result_output: str | Path = "runtime_data/parcels/foundation_result.json",
) -> dict[str, Any]:
    exported = export_receipts(output_path=receipts_output)
    if exported.get("count", 0) <= 0:
        return {"ok": False, "reason": "no receipts", "exported": exported}
    core_root = Path(core_path).resolve()
    plan = Path(plan_path).resolve()
    receipts = Path(receipts_output).resolve()
    ckpt_set = Path(set_output).resolve()
    result = Path(result_output).resolve()
    set_info = run_json([sys.executable, str(core_root / "scripts" / "finalize_receipts.py"), str(plan), str(receipts), "--output", str(ckpt_set)], cwd=core_root)
    artifact_info = run_json([sys.executable, str(core_root / "scripts" / "make_artifact.py"), str(plan), str(ckpt_set), "--output", str(result)], cwd=core_root)
    return {"ok": True, "exported": exported, "checkpoint_set": set_info, "artifact": artifact_info, "result_output": str(result)}


def build_and_apply(plan_path: str | Path, core_path: str | Path = "../ailovanta-core", result_output: str | Path = "runtime_data/parcels/foundation_result.json") -> dict[str, Any]:
    built = build_result(plan_path=plan_path, core_path=core_path, result_output=result_output)
    if not built.get("ok"):
        return {"ok": False, "stage": "build", "build": built}
    applied = apply_result(built["result_output"])
    return {"ok": bool(applied.get("ok")), "build": built, "apply": applied}
