from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

from api.foundation_job_store import FoundationJobStore

EXPORT_SCHEMA = "ailovanta.verified_code_sample_export.v1"


def load_verified_code_export(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != EXPORT_SCHEMA:
        raise ValueError("unsupported verified code sample export schema")
    if not isinstance(payload.get("samples"), list):
        raise ValueError("verified code sample export has no samples list")
    return payload


def sample_to_training_row(sample: dict[str, Any]) -> dict[str, Any]:
    if sample.get("schema_version") != "ailovanta.verified_code_sample.v1":
        raise ValueError("unsupported verified code sample schema")
    instruction = str(sample.get("instruction") or "").strip()
    output = expected_output(sample)
    if not instruction or not output.strip():
        raise ValueError("verified code sample is missing instruction or output")
    return {
        "instruction": instruction,
        "output": output,
        "context_files": sample.get("context_files") or {},
        "candidate_files": sample.get("candidate_files") or {},
        "verification": sample.get("verification") or {},
        "source": sample.get("source") or {},
        "task_id": sample.get("task_id"),
        "sample_hash": sample.get("sample_hash"),
        "training_kind": "verified_code_sft",
    }


def expected_output(sample: dict[str, Any]) -> str:
    expected = sample.get("expected_response")
    if expected:
        return str(expected)
    candidates = sample.get("candidate_files") if isinstance(sample.get("candidate_files"), dict) else {}
    if candidates:
        return "\n\n".join(f"### {path}\n{content}" for path, content in sorted(candidates.items()))
    return ""


def export_to_dataset_shard(
    payload: dict[str, Any],
    output_dir: str | Path = "runtime_data/verified_code_datasets",
    dataset_id: str | None = None,
) -> dict[str, Any]:
    if payload.get("schema_version") != EXPORT_SCHEMA:
        raise ValueError("unsupported verified code sample export schema")
    rows = [sample_to_training_row(sample) for sample in payload.get("samples", [])]
    if not rows:
        raise ValueError("verified code sample export has no usable rows")

    export_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    dataset_name = dataset_id or f"verified_code_{export_hash}"
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    dataset_path = output_root / f"{dataset_name}.jsonl"
    dataset_path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
    artifact_hash = "sha256:" + hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    return {
        "shard_id": "verified_code_shard_" + export_hash,
        "source_id": dataset_name,
        "uri": "file://" + str(dataset_path.resolve()),
        "token_count": max(1, sum(len(json.dumps(row, ensure_ascii=False).split()) for row in rows)),
        "allowed_use": "verified_code_sft",
        "artifact_hash": artifact_hash,
        "row_count": len(rows),
        "dataset_path": str(dataset_path),
    }


def build_job_from_verified_code_export(
    payload: dict[str, Any],
    model_id: str = "ailovanta-code",
    target_version: str = "candidate",
    node_id: str = "verified_code_node_1",
    gpu_memory_gb: float = 24.0,
    max_steps: int = 100,
    execute_checkpoints: bool = True,
    dataset_output_dir: str | Path = "runtime_data/verified_code_datasets",
) -> dict[str, Any]:
    shard = export_to_dataset_shard(payload, output_dir=dataset_output_dir)
    job = {
        "schema_version": "ailovanta.foundation_job.v1",
        "model": {"model_id": model_id, "target_version": target_version, "parameter_count_b": 1.0, "context_length": 8192},
        "dataset_shards": [{key: value for key, value in shard.items() if key not in {"row_count", "dataset_path"}}],
        "nodes": [{"node_id": node_id, "gpu_memory_gb": gpu_memory_gb, "gpu_count": 1, "trust_score": 0.95, "region": "local"}],
        "stage": "verified_code_sft",
        "max_steps": max_steps,
        "status": "queued",
        "metadata": {
            "source": "verified_code_samples",
            "sample_count": int(payload.get("count") or len(payload.get("samples", []))),
            "row_count": shard["row_count"],
            "dataset_path": shard["dataset_path"],
            "created_at": round(time(), 3),
        },
    }
    if execute_checkpoints:
        job["execute_checkpoints"] = True
    return job


def create_job_from_verified_code_export(
    export_path: str | Path,
    job_store: FoundationJobStore | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    payload = load_verified_code_export(export_path)
    job = build_job_from_verified_code_export(payload, **kwargs)
    return (job_store or FoundationJobStore()).create(job)
