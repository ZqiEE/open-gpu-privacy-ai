from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from api.storage import SchedulerStore
from api.training_job_export import export_training_job


def run_training_pipeline(
    job_id: str,
    core_path: str | Path | None = None,
    work_dir: str | Path = "runtime_data/training_pipeline",
    store: SchedulerStore | None = None,
) -> dict[str, Any]:
    core_root = Path(core_path or os.getenv("AILOVANTA_CORE_PATH", "../ailovanta-core")).resolve()
    if not core_root.exists():
        raise ValueError("ailovanta-core path not found: " + str(core_root))

    scheduler = store or SchedulerStore()
    output_root = Path(work_dir)
    exports_dir = output_root / "exports"
    core_output_dir = output_root / "core_bridge"

    exported = export_training_job(job_id, exports_dir, store=scheduler)
    export_path = Path(exported["export_path"]).resolve()

    command = [
        sys.executable,
        str(core_root / "scripts" / "run_public_bridge.py"),
        str(export_path),
        "--output-dir",
        str(core_output_dir.resolve()),
    ]
    completed = subprocess.run(command, cwd=core_root, check=True, capture_output=True, text=True)
    core_result = json.loads(completed.stdout)

    model_name = str(core_result.get("next_model_version") or f"ailovanta-local-{job_id}")
    model_record = scheduler.register_model_version(
        {
            "model_id": f"model_{model_name.lower().replace(' ', '_')}_{job_id}",
            "name": model_name,
            "base_model": str(core_result.get("base_model") or exported["payload"].get("base_model") or "unknown"),
            "source_job_id": job_id,
            "notes": str(core_result.get("result_path") or ""),
        }
    )

    return {
        "ok": True,
        "job_id": job_id,
        "core_path": str(core_root),
        "export_path": str(export_path),
        "core_result": core_result,
        "model_version": model_record,
    }
