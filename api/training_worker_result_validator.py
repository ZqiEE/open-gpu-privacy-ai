from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite

TRAINING_WORKER_RESULT_SCHEMA = "ailovanta.training_worker_result.v1"
TRAINING_WORKER_RECEIPT_SCHEMA = "ailovanta.training_worker_result_receipt.v1"
REAL_BACKENDS = {"transformers", "lora", "qlora"}


class TrainingWorkerResultStore:
    def __init__(self, path: str | Path = "runtime_data/training_worker_result_receipts.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS training_worker_result_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    result_hash TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    score REAL NOT NULL,
                    blockers_json TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_training_worker_receipts_node ON training_worker_result_receipts(node_id);
                CREATE INDEX IF NOT EXISTS idx_training_worker_receipts_job ON training_worker_result_receipts(job_id);
                CREATE INDEX IF NOT EXISTS idx_training_worker_receipts_artifact ON training_worker_result_receipts(artifact_hash);
                """
            )

    def add(self, receipt: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO training_worker_result_receipts (
                    receipt_id, result_hash, node_id, job_id, artifact_hash,
                    passed, score, blockers_json, receipt_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt["receipt_id"],
                    receipt["result_hash"],
                    receipt["node_id"],
                    receipt["job_id"],
                    receipt.get("artifact_hash") or "",
                    1 if receipt["passed"] else 0,
                    receipt["score"],
                    json.dumps(receipt.get("blockers", []), ensure_ascii=False),
                    json.dumps(receipt, ensure_ascii=False),
                ),
            )
        return self.get(receipt["receipt_id"]) or {}

    def get(self, receipt_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM training_worker_result_receipts WHERE receipt_id = ?", (receipt_id,)).fetchone()
        if not row:
            return None
        receipt = json.loads(dict(row)["receipt_json"])
        receipt["created_at"] = dict(row)["created_at"]
        return receipt

    def list(self, node_id: str | None = None, job_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if node_id:
                rows = conn.execute("SELECT * FROM training_worker_result_receipts WHERE node_id = ? ORDER BY created_at DESC LIMIT ?", (node_id, limit)).fetchall()
            elif job_id:
                rows = conn.execute("SELECT * FROM training_worker_result_receipts WHERE job_id = ? ORDER BY created_at DESC LIMIT ?", (job_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM training_worker_result_receipts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        receipts = []
        for row in rows:
            item = json.loads(dict(row)["receipt_json"])
            item["created_at"] = dict(row)["created_at"]
            receipts.append(item)
        return receipts


def build_training_worker_result(
    *,
    job: dict[str, Any],
    node_id: str,
    profile: dict[str, Any],
    output: dict[str, Any],
    binding: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    job_id = str(job.get("job_id") or job.get("id") or "")
    metadata = binding.get("metadata") if isinstance(binding, dict) and isinstance(binding.get("metadata"), dict) else {}
    distribution = metadata.get("artifact_distribution") if isinstance(metadata.get("artifact_distribution"), dict) else {}
    return {
        "schema_version": TRAINING_WORKER_RESULT_SCHEMA,
        "job_id": job_id,
        "job_type": str(job.get("job_type") or job.get("type") or payload.get("kind") or ""),
        "node_id": node_id,
        "node_profile": {
            "device_name": profile.get("device_name"),
            "cpu_threads": profile.get("cpu_threads"),
            "memory_gb": profile.get("memory_gb"),
            "has_gpu": bool(profile.get("has_gpu")),
            "gpu_name": profile.get("gpu_name"),
        },
        "training_request": _compact_payload(payload),
        "training_output": {
            "name": output.get("name"),
            "version": output.get("version"),
            "source_job_id": output.get("source_job_id"),
            "location": output.get("location"),
            "kind": output.get("kind"),
            "status": output.get("status"),
            "metrics": output.get("metrics"),
            "notes": output.get("notes"),
            "training_runtime_evidence": output.get("training_runtime_evidence"),
        },
        "artifact_binding": _compact_binding(binding),
        "artifact_distribution": {
            "artifact_id": distribution.get("artifact_id"),
            "model_artifact_hash": distribution.get("model_artifact_hash"),
            "storage_artifact_hash": distribution.get("storage_artifact_hash"),
            "manifest_hash": distribution.get("manifest_hash"),
            "manifest_uri": distribution.get("manifest_uri"),
            "sealed": distribution.get("sealed"),
        },
        "created_at": round(time(), 3),
    }


def validate_training_worker_result(
    worker_result: dict[str, Any],
    *,
    store: TrainingWorkerResultStore | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if worker_result.get("schema_version") != TRAINING_WORKER_RESULT_SCHEMA:
        blockers.append("unsupported_training_worker_result_schema")
    node_id = str(worker_result.get("node_id") or "")
    job_id = str(worker_result.get("job_id") or "")
    request = worker_result.get("training_request") if isinstance(worker_result.get("training_request"), dict) else {}
    output = worker_result.get("training_output") if isinstance(worker_result.get("training_output"), dict) else {}
    binding = worker_result.get("artifact_binding") if isinstance(worker_result.get("artifact_binding"), dict) else {}
    evidence = output.get("training_runtime_evidence") if isinstance(output.get("training_runtime_evidence"), dict) else {}

    if not node_id:
        blockers.append("missing_node_id")
    if not job_id:
        blockers.append("missing_job_id")
    if not output:
        blockers.append("missing_training_output")
    if output.get("status") == "failed":
        blockers.append("training_output_failed")
    if output.get("status") != "candidate":
        blockers.append("training_output_not_candidate")

    requested_real = bool(request.get("real") or request.get("use_transformers") or request.get("peft") or request.get("qlora"))
    if requested_real:
        if not evidence:
            blockers.append("missing_training_runtime_evidence")
        else:
            if evidence.get("requested_real_training") is not True:
                blockers.append("runtime_evidence:not_real_training_request")
            if evidence.get("real_training_executed") is not True:
                blockers.append("runtime_evidence:real_training_not_executed")
            if evidence.get("fallback_used"):
                blockers.append("runtime_evidence:fallback_used")
            if str(evidence.get("actual_backend") or "") not in REAL_BACKENDS:
                blockers.append("runtime_evidence:unsupported_real_backend")
            if request.get("requires_gpu") or evidence.get("requires_gpu"):
                if evidence.get("gpu_execution_evidence") is not True:
                    blockers.append("runtime_evidence:gpu_execution_unproven")

    artifact_hash = str(binding.get("artifact_hash") or "")
    if output.get("status") == "candidate":
        if not binding:
            blockers.append("missing_artifact_binding")
        if not artifact_hash.startswith("sha256:"):
            blockers.append("missing_artifact_hash")
        if binding and binding.get("source_job_id") and binding.get("source_job_id") != output.get("source_job_id"):
            blockers.append("source_job_id_mismatch")

    blockers = sorted(set(blockers))
    score = max(0.0, round(1.0 - 0.2 * len(blockers), 3))
    receipt = {
        "schema_version": TRAINING_WORKER_RECEIPT_SCHEMA,
        "receipt_id": "twr_" + uuid4().hex[:12],
        "result_hash": stable_hash(worker_result),
        "node_id": node_id,
        "job_id": job_id,
        "artifact_hash": artifact_hash,
        "artifact_binding_id": binding.get("binding_id"),
        "passed": not blockers,
        "score": score,
        "blockers": blockers,
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    if store is not None:
        receipt = store.add(receipt)
    return receipt


def stable_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "kind",
        "name",
        "dataset_uri",
        "base_model",
        "max_steps",
        "real",
        "use_transformers",
        "peft",
        "lora",
        "qlora",
        "requires_gpu",
        "allow_lightweight_fallback",
        "priority",
    ]
    return {key: payload.get(key) for key in keys if key in payload}


def _compact_binding(binding: dict[str, Any] | None) -> dict[str, Any]:
    if not binding:
        return {}
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    return {
        "binding_id": binding.get("binding_id"),
        "model_key": binding.get("model_key"),
        "backend_kind": binding.get("backend_kind"),
        "backend_ref": binding.get("backend_ref"),
        "artifact_hash": binding.get("artifact_hash"),
        "status": binding.get("status"),
        "source_job_id": metadata.get("source_job_id"),
        "promotion_gate": metadata.get("promotion_gate"),
    }
