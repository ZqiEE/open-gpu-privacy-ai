from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.runtime_ref import check_runtime_ref
from api.runtime_router import ModelManifest, RuntimeNodeProfile
from api.runtime_store import RuntimeStore


@dataclass(frozen=True)
class WarmSpec:
    model_key: str = "ailovanta-owned:candidate"
    runtime_id: str = "rt-owned-1"
    node_id: str = "node-owned-1"
    gpu_memory_gb: float = 24.0
    region: str = "global"


class ModelWarm:
    def __init__(
        self,
        bindings: ArtifactBindingStore | None = None,
        runtime: RuntimeStore | None = None,
        chain: ChainRegistry | None = None,
    ) -> None:
        self.bindings = bindings or ArtifactBindingStore()
        self.runtime = runtime or RuntimeStore()
        self.chain = chain or ChainRegistry()

    def run(self, spec: WarmSpec) -> dict[str, Any]:
        binding = self.bindings.latest_for_model(spec.model_key, active_only=True)
        if not binding:
            return {"ok": False, "reason": "no usable model binding", "model_key": spec.model_key}
        report = check_runtime_ref(binding)
        if not report.get("ready"):
            return {"ok": False, "reason": "model ref not ready", "model_key": spec.model_key, "report": report}
        status = "active" if binding.get("status") == "active" else "candidate"
        model = self.runtime.register_model(
            ModelManifest(
                model_id=binding["model_id"],
                version=binding["version"],
                manifest_hash=binding["runtime_manifest_hash"],
                privacy_level="protected",
                min_gpu_memory_gb=0.0,
                allowed_pools=["trusted_runtime_pool", "enterprise_pool"],
                quantization=binding.get("backend_kind") or "artifact",
                context_length=8192,
                adapter_compatible=True,
                status=status,
            )
        )
        node = self.runtime.register_runtime(
            RuntimeNodeProfile(
                runtime_id=spec.runtime_id,
                node_id=spec.node_id,
                pool="trusted_runtime_pool",
                region=spec.region,
                status="online",
                gpu_memory_gb=spec.gpu_memory_gb,
                available_gpu_memory_gb=spec.gpu_memory_gb,
                trust_score=0.95,
                current_load=0.0,
                price_per_1k_tokens=0.0,
                latency_ms=200,
                supported_engines=["ailovanta-worker"],
                cached_models=[spec.model_key],
                cached_adapters=[],
            )
        )
        event = self.chain.append_model_event(
            {
                "event_type": "runtime_model_warmed",
                "model_id": binding["model_id"],
                "version": binding["version"],
                "artifact_hash": binding["artifact_hash"],
                "runtime_manifest_hash": binding["runtime_manifest_hash"],
                "metadata": {
                    "binding_id": binding["binding_id"],
                    "runtime_id": spec.runtime_id,
                    "node_id": spec.node_id,
                    "backend_ref": binding.get("backend_ref"),
                },
            }
        )
        return {"ok": True, "binding": binding, "ref_check": report, "model": model, "node": node, "chain_event": event}
