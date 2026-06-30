from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from api.foundation_job_export import export_foundation_job
from api.foundation_result_import import import_foundation_result_file


def run_foundation_pipeline(
    job_id: str,
    core_path: str | Path | None = None,
    work_dir: str | Path = "runtime_data/foundation_pipeline",
    execute_checkpoints: bool = False,
    checkpoint_output_root: str | Path | None = None,
    training_command: str | None = None,
) -> dict[str, Any]:
    core_root = Path(core_path or os.getenv("AILOVANTA_CORE_PATH", "../ailovanta-core")).resolve()
    if not core_root.exists():
        raise ValueError("ailovanta-core path not found: " + str(core_root))

    output_root = Path(work_dir)
    exports_dir = output_root / "exports"
    results_dir = output_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    exported = export_foundation_job(job_id, exports_dir)
    export_path = Path(exported["export_path"]).resolve()
    result_path = (results_dir / f"{job_id}_foundation_result.json").resolve()

    command = [
        sys.executable,
        str(core_root / "scripts" / "run_foundation_job.py"),
        str(export_path),
        "--output",
        str(result_path),
    ]
    if execute_checkpoints:
        command.append("--execute-checkpoints")
    if checkpoint_output_root:
        command.extend(["--checkpoint-output-root", str(Path(checkpoint_output_root).resolve())])
    if training_command:
        command.extend(["--training-command", training_command])
    subprocess.run(command, cwd=core_root, check=True)

    imported = import_foundation_result_file(result_path)
    return {
        "ok": True,
        "job_id": job_id,
        "core_path": str(core_root),
        "export_path": str(export_path),
        "result_path": str(result_path),
        "execute_checkpoints": execute_checkpoints,
        "import_result": imported,
    }


def write_pipeline_result(result: dict[str, Any], output_path: str | Path) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
