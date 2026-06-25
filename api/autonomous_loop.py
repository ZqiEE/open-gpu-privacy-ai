from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.autotruth_store import AutoTruthEventStore
from api.learning_gate import run_guarded_learning_pipeline


class AutonomousLoop:
    def __init__(self, core_path: str | Path | None = None, root: str | Path = "runtime_data/autonomous_loop") -> None:
        self.core_root = Path(core_path or os.getenv("AILOVANTA_CORE_PATH", "../ailovanta-core")).resolve()
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def run_once(
        self,
        baseline_model: str = "ailovanta-owned:baseline",
        baseline_score: float = 0.45,
        allow_shadow_import: bool = False,
        execute_checkpoints: bool = False,
        checkpoint_output_root: str | Path | None = None,
        training_command: str | None = None,
        model_backend: str | None = None,
        base_model: str | None = None,
        backend_output_dir: str | Path | None = None,
        backend_device: str | None = None,
        backend_max_steps: int | None = None,
        backend_lr: float | None = None,
        max_steps: int = 100,
        model_id: str = "ailovanta-owned",
        target_version: str = "candidate",
    ) -> dict[str, Any]:
        if not self.core_root.exists():
            raise ValueError("ailovanta-core path not found: " + str(self.core_root))
        run_id = "auto_" + uuid4().hex[:12]
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        store = AutoTruthEventStore()
        export_path = run_dir / "events.json"
        exported = store.export_events(export_path)

        score_path = run_dir / "autotruth_result.json"
        subprocess.run(
            [sys.executable, str(self.core_root / "scripts" / "run_autotruth.py"), str(export_path), "--output", str(score_path)],
            cwd=self.core_root,
            check=True,
        )
        scored = json.loads(score_path.read_text(encoding="utf-8"))
        imported = store.import_run(scored)

        guarded = run_guarded_learning_pipeline(
            core_path=self.core_root,
            work_dir=run_dir / "guarded",
            baseline_model=baseline_model,
            baseline_score=baseline_score,
            allow_shadow_import=allow_shadow_import,
            execute_checkpoints=execute_checkpoints,
            checkpoint_output_root=checkpoint_output_root or (run_dir / "checkpoints"),
            training_command=training_command,
            model_backend=model_backend,
            base_model=base_model,
            backend_output_dir=backend_output_dir or (run_dir / "model_backend"),
            backend_device=backend_device,
            backend_max_steps=backend_max_steps,
            backend_lr=backend_lr,
            model_id=model_id,
            target_version=target_version,
            max_steps=max_steps,
        )

        payload = {
            "run_id": run_id,
            "ok": True,
            "event_export": exported,
            "autotruth_result_path": str(score_path),
            "autotruth_rows": len(scored.get("rows", [])),
            "training_pack": scored.get("training_pack", {}),
            "public_import": imported,
            "execute_checkpoints": execute_checkpoints,
            "guarded": guarded,
            "created_at": round(time(), 3),
        }
        self._write_run(payload)
        return payload

    def latest_run(self) -> dict[str, Any] | None:
        rows = sorted(self.runs_dir.glob("*/run.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return json.loads(rows[0].read_text(encoding="utf-8")) if rows else None

    def list_runs(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.runs_dir.glob("*/run.json"))]

    def _write_run(self, payload: dict[str, Any]) -> None:
        run_dir = self.runs_dir / payload["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
