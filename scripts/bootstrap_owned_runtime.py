from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.artifact_binding import ArtifactBindingStore
from api.node_trust import NodeTrustStore
from api.runtime_forwarder import RuntimeEndpointStore
from api.runtime_router import ModelManifest, RuntimeNodeProfile
from api.runtime_store import RuntimeStore


def bootstrap_owned_runtime(
    root: str | Path = "runtime_data",
    model_id: str = "ailovanta-owned",
    version: str = "candidate",
    runtime_id: str = "rt-owned-1",
    node_id: str = "node-owned-1",
) -> dict:
    data_root = Path(root)
    data_root.mkdir(parents=True, exist_ok=True)
    checkpoint = data_root / "owned_runtime_checkpoint.json"
    checkpoint_payload = {
        "backend": "jsonl-stat",
        "token_count": 0,
        "train_loss": None,
        "eval_loss": None,
        "note": "local owned-runtime bootstrap checkpoint; replace with a foundation artifact after training",
    }
    checkpoint.write_text(json.dumps(checkpoint_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    checkpoint_ref = "file://" + str(checkpoint.resolve())
    manifest_hash = "sha256:local-owned-candidate"

    runtime = RuntimeStore(data_root / "runtime.sqlite3")
    model = runtime.register_model(
        ModelManifest(
            model_id=model_id,
            version=version,
            manifest_hash=manifest_hash,
            privacy_level="protected",
            min_gpu_memory_gb=0,
            allowed_pools=["trusted_runtime_pool", "enterprise_pool"],
            quantization="local",
            context_length=8192,
            adapter_compatible=True,
            status="active",
        )
    )
    node = runtime.register_runtime(
        RuntimeNodeProfile(
            runtime_id=runtime_id,
            node_id=node_id,
            pool="trusted_runtime_pool",
            region="global",
            status="online",
            gpu_memory_gb=24,
            available_gpu_memory_gb=24,
            trust_score=0.95,
            current_load=0,
            price_per_1k_tokens=0,
            latency_ms=100,
            supported_engines=["ailovanta-worker"],
            cached_models=[f"{model_id}:{version}"],
        )
    )
    trust = NodeTrustStore(data_root / "node_trust.sqlite3").register(node_id, "local-bootstrap", trust_score=0.95, metadata={"source": "bootstrap_owned_runtime"})
    endpoint = RuntimeEndpointStore(data_root / "runtime_endpoints.json").register(runtime_id, "inprocess://ailovanta-worker")
    artifact = {
        "artifact_id": "local_owned_runtime_bootstrap",
        "artifact_hash": manifest_hash,
        "checkpoint_uri": checkpoint_ref,
        "backend_ref": checkpoint_ref,
        "backend_kind": "checkpoint-artifact",
    }
    binding_store = ArtifactBindingStore(data_root / "artifact_bindings.sqlite3")
    existing_binding = binding_store.latest_for_model(f"{model_id}:{version}", active_only=True)
    if existing_binding and existing_binding.get("backend_kind") != "checkpoint-artifact":
        binding = existing_binding
    else:
        binding = binding_store.register_binding(
            model,
            artifact,
            backend_kind="checkpoint-artifact",
            backend_ref=checkpoint_ref,
            status="active",
            metadata={"source": "bootstrap_owned_runtime", "runtime_id": runtime_id, "node_id": node_id},
        )
    return {
        "ok": True,
        "model": model,
        "runtime": node,
        "node_trust": trust,
        "endpoint": endpoint,
        "binding": binding,
        "checkpoint_ref": checkpoint_ref,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a local owned runtime using the in-process worker")
    parser.add_argument("--root", default="runtime_data")
    parser.add_argument("--model-id", default="ailovanta-owned")
    parser.add_argument("--version", default="candidate")
    parser.add_argument("--runtime-id", default="rt-owned-1")
    parser.add_argument("--node-id", default="node-owned-1")
    args = parser.parse_args()
    result = bootstrap_owned_runtime(args.root, args.model_id, args.version, args.runtime_id, args.node_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
