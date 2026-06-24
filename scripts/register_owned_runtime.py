from __future__ import annotations

import os
import sys

import httpx


def post_json(base_url: str, path: str, payload: dict) -> dict:
    with httpx.Client(timeout=20) as client:
        response = client.post(base_url.rstrip("/") + path, json=payload)
        response.raise_for_status()
        return response.json()


def main() -> int:
    api_url = os.getenv("AILOVANTA_API_URL", "http://127.0.0.1:8000").rstrip("/")
    model_id = os.getenv("AILOVANTA_OWNED_MODEL_ID", "ailovanta-owned")
    version = os.getenv("AILOVANTA_OWNED_MODEL_VERSION", "candidate")
    manifest_hash = os.getenv("AILOVANTA_OWNED_MANIFEST_HASH", "sha256:local-owned-candidate")
    artifact_hash = os.getenv("AILOVANTA_OWNED_ARTIFACT_HASH", manifest_hash)
    runtime_id = os.getenv("AILOVANTA_RUNTIME_ID", "rt-owned-1")
    node_id = os.getenv("AILOVANTA_NODE_ID", "node-owned-1")

    model = post_json(
        api_url,
        "/runtime/models/register",
        {
            "model_id": model_id,
            "version": version,
            "manifest_hash": manifest_hash,
            "privacy_level": "protected",
            "min_gpu_memory_gb": 0,
            "allowed_pools": ["trusted_runtime_pool", "enterprise_pool"],
            "quantization": "local",
            "context_length": 8192,
            "adapter_compatible": True,
            "status": "active",
        },
    )

    node = post_json(
        api_url,
        "/runtime/nodes/register",
        {
            "runtime_id": runtime_id,
            "node_id": node_id,
            "pool": "trusted_runtime_pool",
            "region": "global",
            "status": "online",
            "gpu_memory_gb": 24,
            "available_gpu_memory_gb": 24,
            "trust_score": 0.95,
            "current_load": 0,
            "price_per_1k_tokens": 0,
            "latency_ms": 200,
            "supported_engines": ["ailovanta-worker"],
            "cached_models": [model_id + ":" + version],
            "cached_adapters": [],
        },
    )

    chain_event = post_json(
        api_url,
        "/chain/events",
        {
            "event_type": "runtime_manifest_registered",
            "model_id": model_id,
            "version": version,
            "artifact_hash": artifact_hash,
            "runtime_manifest_hash": manifest_hash,
            "metadata": {"runtime_id": runtime_id, "node_id": node_id},
        },
    )

    print("registered model", model)
    print("registered runtime", node)
    print("registered chain event", chain_event)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("owned runtime registration failed", exc, file=sys.stderr)
        raise SystemExit(1)
