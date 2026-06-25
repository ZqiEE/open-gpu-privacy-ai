from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

from api.autotruth_store import AutoTruthEventStore
from api.foundation_job_store import FoundationJobStore


def pack_to_dataset_shard(pack: dict[str, Any], output_dir: str | Path = "runtime_data/learning_datasets") -> dict[str, Any]:
    pack_id = pack.get("pack_id")
    if not pack_id:
        raise ValueError("training pack has no pack_id")
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    dataset_path = output_root / f"{pack_id}.jsonl"
    rows = []
    for item in pack.get("sft", []):
        rows.append({"instruction": item.get("instruction", ""), "output": item.get("output", ""), "score": item.get("score", 0.0), "sample_id": item.get("sample_id")})
    for item in pack.get("dpo", []):
        rows.append({"prompt": item.get("prompt", ""), "chosen": item.get("chosen", ""), "rejected": item.get("rejected", ""), "chosen_id": item.get("chosen_id"), "rejected_id": item.get("rejected_id")})
    if not rows:
        raise ValueError("training pack has no usable rows")
    dataset_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    digest = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    return {
        "shard_id": "learning_shard_" + pack_id,
        "source_id": pack_id,
        "uri": "file://" + str(dataset_path.resolve()),
        "token_count": max(1, sum(len(json.dumps(row, ensure_ascii=False).split()) for row in rows)),
        "allowed_use": "sft",
        "artifact_hash": "sha256:" + digest,
    }


def build_job_from_pack(
    pack: dict[str, Any],
    model_id: str = "ailovanta-owned",
    target_version: str = "candidate",
    node_id: str = "learning_node_1",
    gpu_memory_gb: float = 24.0,
    max_steps: int = 100,
) -> dict[str, Any]:
    shard = pack_to_dataset_shard(pack)
    return {
        "schema_version": "ailovanta.foundation_job.v1",
        "model": {"model_id": model_id, "target_version": target_version, "parameter_count_b": 1.0, "context_length": 8192},
        "dataset_shards": [shard],
        "nodes": [{"node_id": node_id, "gpu_memory_gb": gpu_memory_gb, "gpu_count": 1, "trust_score": 0.9, "region": "local"}],
        "stage": "sft",
        "max_steps": max_steps,
        "status": "queued",
        "metadata": {"source": "autotruth_learning_pack", "pack_id": pack.get("pack_id"), "pack_hash": pack.get("pack_hash"), "created_at": round(time(), 3)},
    }


def create_job_from_latest_pack(
    event_store: AutoTruthEventStore | None = None,
    job_store: FoundationJobStore | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    pack = (event_store or AutoTruthEventStore()).latest_pack()
    if not pack:
        raise ValueError("no latest training pack")
    payload = build_job_from_pack(pack, **kwargs)
    return (job_store or FoundationJobStore()).create(payload)
