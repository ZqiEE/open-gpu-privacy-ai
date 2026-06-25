from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


PUBLIC_MODULES = [
    "api.node_trust",
    "api.node_proof",
    "api.parcel_receipts",
    "api.g2",
    "api.ra2",
    "api.final_report",
]

CORE_SCRIPTS = [
    "scripts/finalize_receipts.py",
    "scripts/make_artifact_v2.py",
    "scripts/run_eval_gate.py",
]


def module_ok(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def check(core_path: str | Path = "../ailovanta-core") -> dict[str, Any]:
    core = Path(core_path).resolve()
    blockers: list[str] = []
    modules = {name: module_ok(name) for name in PUBLIC_MODULES}
    for name, ok in modules.items():
        if not ok:
            blockers.append("missing_module:" + name)
    scripts = {item: (core / item).exists() for item in CORE_SCRIPTS}
    for name, ok in scripts.items():
        if not ok:
            blockers.append("missing_core_script:" + name)
    runtime_root = Path("runtime_data")
    try:
        runtime_root.mkdir(parents=True, exist_ok=True)
        writable = True
    except Exception:
        writable = False
        blockers.append("runtime_data_not_writable")
    return {"ok": not blockers, "blockers": blockers, "core_path": str(core), "modules": modules, "core_scripts": scripts, "runtime_data_writable": writable}
