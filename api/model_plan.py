from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ModelShard:
    shard_id: str
    data_uri: str
    token_start: int
    token_count: int
    data_hash: str


@dataclass(frozen=True)
class ModelPlan:
    plan_id: str
    model_id: str
    version: str
    data_uri: str
    total_tokens: int
    shard_tokens: int
    min_gpu_memory_gb: float
    stage: str
    shards: list[ModelShard]

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "plan_id": self.plan_id,
            "model_id": self.model_id,
            "version": self.version,
            "data_uri": self.data_uri,
            "total_tokens": self.total_tokens,
            "shard_tokens": self.shard_tokens,
            "min_gpu_memory_gb": self.min_gpu_memory_gb,
            "stage": self.stage,
            "shards": [shard.__dict__ for shard in self.shards],
        }
        payload["plan_hash"] = hash_payload(payload)
        return payload


def build_model_plan(model_id: str, version: str, data_uri: str, total_tokens: int, shard_tokens: int = 8192, min_gpu_memory_gb: float = 8.0, stage: str = "train") -> ModelPlan:
    if total_tokens <= 0:
        raise ValueError("total_tokens must be positive")
    if shard_tokens <= 0:
        raise ValueError("shard_tokens must be positive")
    plan_id = "plan_" + uuid4().hex[:12]
    shards: list[ModelShard] = []
    for index, start in enumerate(range(0, total_tokens, shard_tokens)):
        count = min(shard_tokens, total_tokens - start)
        raw = {"data_uri": data_uri, "token_start": start, "token_count": count}
        shards.append(ModelShard(f"{plan_id}_{index:05d}", data_uri, start, count, hash_payload(raw)))
    return ModelPlan(plan_id, model_id, version, data_uri, total_tokens, shard_tokens, min_gpu_memory_gb, stage, shards)


def jobs_for_plan(plan: ModelPlan) -> list[dict[str, Any]]:
    return [
        {
            "job_id": shard.shard_id,
            "job_type": "model_shard",
            "payload": {
                "plan_id": plan.plan_id,
                "model_id": plan.model_id,
                "version": plan.version,
                "stage": plan.stage,
                "data_uri": shard.data_uri,
                "token_start": shard.token_start,
                "token_count": shard.token_count,
                "data_hash": shard.data_hash,
                "requires_gpu": True,
                "min_gpu_memory_gb": plan.min_gpu_memory_gb,
            },
        }
        for shard in plan.shards
    ]


def result_record(job: dict[str, Any], node_id: str) -> dict[str, Any]:
    payload = job.get("payload", {})
    raw = {"job_id": job.get("job_id") or job.get("id"), "node_id": node_id, "payload": payload}
    return {"job_id": raw["job_id"], "node_id": node_id, "plan_id": payload.get("plan_id"), "result_hash": hash_payload(raw)}


def combine_results(plan: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    good = [item for item in results if item.get("result_hash")]
    payload = {
        "plan_id": plan["plan_id"],
        "model_id": plan["model_id"],
        "version": plan["version"],
        "accepted_results": len(good),
        "expected_results": len(plan.get("shards", [])),
        "result_hashes": sorted(item["result_hash"] for item in good),
    }
    payload["combined_hash"] = hash_payload(payload)
    payload["complete"] = payload["accepted_results"] == payload["expected_results"] and payload["expected_results"] > 0
    return payload


def hash_payload(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()
