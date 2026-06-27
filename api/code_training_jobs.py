from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.rights_proof_registry import RightsProofRegistry

ALLOWED_CODE_TRAINING_KINDS = {"code_lora", "code_qlora", "code_distill", "code_eval"}
DEFAULT_CODE_JOB_PATH = Path("runtime_data/code_training_jobs.json")


class CodeTrainingJobError(ValueError):
    pass


class CodeTrainingJobStore:
    def __init__(self, path: str | Path = DEFAULT_CODE_JOB_PATH, rights_registry: RightsProofRegistry | None = None) -> None:
        self.path = Path(path)
        self.rights_registry = rights_registry or RightsProofRegistry()

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        return list(payload.get("jobs") or [])

    def _write_all(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_job(self, *, rights_id: str, dataset_id: str, kind: str = "code_lora", base_model: str = "ailovanta-code-bootstrap", target_model: str = "ailovanta-code") -> dict[str, Any]:
        if kind not in ALLOWED_CODE_TRAINING_KINDS:
            raise CodeTrainingJobError(f"unsupported code training kind: {kind}")
        if not rights_id:
            raise CodeTrainingJobError("rights_id is required")
        if not dataset_id:
            raise CodeTrainingJobError("dataset_id is required")

        self.rights_registry.can_train(rights_id, kind)

        job = {
            "schema_version": "ailovanta.training_job.v1",
            "job_id": "train_code_" + uuid4().hex[:12],
            "kind": kind,
            "rights_id": rights_id,
            "dataset_id": dataset_id,
            "base_model": base_model,
            "target_model": target_model,
            "distributed_required": True,
            "node_requirements": {"cpu_nodes": 1, "gpu_nodes": 1, "validator_nodes": 1},
            "validator_requirements": {"pytest": True, "lint": True},
            "promotion_gate": {"min_test_pass_rate": 0.8, "max_regression_rate": 0.05},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        items = self._read_all()
        items.append(job)
        self._write_all(items)
        return job

    def list_jobs(self) -> list[dict[str, Any]]:
        return self._read_all()
