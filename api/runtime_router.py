from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Literal


PrivacyLevel = Literal["public", "protected", "private"]
RuntimePool = Literal["cpu_pool", "small_gpu_pool", "large_gpu_pool", "storage_pool", "validator_pool", "trusted_runtime_pool", "enterprise_pool"]
TaskType = Literal["chat_completion", "embedding", "rerank", "batch", "training", "validation"]


@dataclass
class ModelManifest:
    model_id: str
    version: str
    manifest_hash: str
    privacy_level: PrivacyLevel = "public"
    min_gpu_memory_gb: float = 0.0
    allowed_pools: list[RuntimePool] = field(default_factory=lambda: ["small_gpu_pool", "large_gpu_pool", "enterprise_pool"])
    quantization: str = "unknown"
    context_length: int = 4096
    adapter_compatible: bool = True
    status: str = "active"
    artifact_uri: str = ""
    created_at: float = field(default_factory=time)

    @property
    def key(self) -> str:
        return f"{self.model_id}:{self.version}"


@dataclass
class RuntimeNodeProfile:
    runtime_id: str
    node_id: str
    pool: RuntimePool
    region: str = "global"
    status: str = "online"
    gpu_memory_gb: float = 0.0
    available_gpu_memory_gb: float = 0.0
    trust_score: float = 0.5
    current_load: float = 0.0
    price_per_1k_tokens: float = 0.0
    latency_ms: int = 1000
    supported_engines: list[str] = field(default_factory=list)
    cached_models: list[str] = field(default_factory=list)
    cached_adapters: list[str] = field(default_factory=list)
    last_heartbeat: float = field(default_factory=time)

    def has_warm_model(self, model_key: str) -> bool:
        return model_key in self.cached_models


@dataclass
class RuntimeRequest:
    request_id: str
    model_id: str
    version: str
    task_type: TaskType = "chat_completion"
    privacy_level: PrivacyLevel = "public"
    latency_target_ms: int = 2000
    max_price_per_1k_tokens: float = 0.1
    region_hint: str = "auto"
    required_context_length: int = 4096
    required_adapter: str | None = None
    verification_required: bool = True

    @property
    def model_key(self) -> str:
        return f"{self.model_id}:{self.version}"


@dataclass
class RuntimeAssignment:
    request_id: str
    model_key: str
    runtime_id: str
    node_id: str
    pool: RuntimePool
    region: str
    cache_state: Literal["warm", "cold"]
    model_manifest_hash: str
    artifact_uri: str
    estimated_latency_ms: int
    price_per_1k_tokens: float
    verification_required: bool
    score: float
    reason: str


class RuntimeRegistry:
    def __init__(self) -> None:
        self.models: dict[str, ModelManifest] = {}
        self.runtimes: dict[str, RuntimeNodeProfile] = {}

    def register_model(self, manifest: ModelManifest) -> dict:
        self.models[manifest.key] = manifest
        return asdict(manifest)

    def list_models(self) -> list[dict]:
        return [asdict(item) for item in sorted(self.models.values(), key=lambda model: model.key)]

    def register_runtime(self, profile: RuntimeNodeProfile) -> dict:
        profile.last_heartbeat = time()
        self.runtimes[profile.runtime_id] = profile
        return asdict(profile)

    def list_runtimes(self) -> list[dict]:
        return [asdict(item) for item in sorted(self.runtimes.values(), key=lambda runtime: runtime.runtime_id)]

    def status(self) -> dict:
        online = [runtime for runtime in self.runtimes.values() if runtime.status == "online"]
        warm_links = sum(len(runtime.cached_models) for runtime in self.runtimes.values())
        return {
            "models": len(self.models),
            "runtimes": len(self.runtimes),
            "online_runtimes": len(online),
            "warm_model_links": warm_links,
        }

    def route(self, request: RuntimeRequest) -> dict:
        manifest = self.models.get(request.model_key)
        if manifest is None:
            return {
                "assigned": False,
                "reason": "model manifest not found",
                "request_id": request.request_id,
                "model_key": request.model_key,
            }
        if manifest.status != "active":
            return {
                "assigned": False,
                "reason": "model manifest is not active",
                "request_id": request.request_id,
                "model_key": request.model_key,
            }

        candidates: list[RuntimeAssignment] = []
        for runtime in self.runtimes.values():
            candidate = self._score_runtime(request, manifest, runtime)
            if candidate is not None:
                candidates.append(candidate)

        if not candidates:
            return {
                "assigned": False,
                "reason": "no eligible runtime",
                "request_id": request.request_id,
                "model_key": request.model_key,
                "model_manifest_hash": manifest.manifest_hash,
                "artifact_uri": manifest.artifact_uri,
            }

        best = sorted(candidates, key=lambda item: item.score, reverse=True)[0]
        return {"assigned": True, "assignment": asdict(best)}

    def _score_runtime(self, request: RuntimeRequest, manifest: ModelManifest, runtime: RuntimeNodeProfile) -> RuntimeAssignment | None:
        if runtime.status != "online":
            return None
        if runtime.pool not in manifest.allowed_pools:
            return None
        if manifest.privacy_level == "private" and runtime.pool not in {"trusted_runtime_pool", "enterprise_pool"}:
            return None
        if request.privacy_level == "private" and runtime.pool not in {"trusted_runtime_pool", "enterprise_pool"}:
            return None
        if runtime.available_gpu_memory_gb < manifest.min_gpu_memory_gb:
            return None
        if runtime.price_per_1k_tokens > request.max_price_per_1k_tokens:
            return None

        warm = runtime.has_warm_model(manifest.key)
        cache_score = 45.0 if warm else 5.0
        trust_score = max(0.0, min(runtime.trust_score, 1.0)) * 20.0
        load_score = max(0.0, 1.0 - min(runtime.current_load, 1.0)) * 10.0
        latency_score = max(0.0, 1.0 - (runtime.latency_ms / max(request.latency_target_ms, 1))) * 10.0
        price_score = max(0.0, 1.0 - (runtime.price_per_1k_tokens / max(request.max_price_per_1k_tokens, 0.0001))) * 5.0
        region_score = 5.0 if request.region_hint in {"auto", runtime.region} else 0.0
        privacy_score = 5.0 if self._privacy_match(request.privacy_level, manifest.privacy_level, runtime.pool) else 0.0
        score = cache_score + trust_score + load_score + latency_score + price_score + region_score + privacy_score

        reason = "warm runtime selected" if warm else "eligible cold runtime selected"
        return RuntimeAssignment(
            request_id=request.request_id,
            model_key=manifest.key,
            runtime_id=runtime.runtime_id,
            node_id=runtime.node_id,
            pool=runtime.pool,
            region=runtime.region,
            cache_state="warm" if warm else "cold",
            model_manifest_hash=manifest.manifest_hash,
            artifact_uri=manifest.artifact_uri,
            estimated_latency_ms=runtime.latency_ms,
            price_per_1k_tokens=runtime.price_per_1k_tokens,
            verification_required=request.verification_required,
            score=round(score, 4),
            reason=reason,
        )

    @staticmethod
    def _privacy_match(request_privacy: PrivacyLevel, manifest_privacy: PrivacyLevel, runtime_pool: RuntimePool) -> bool:
        if request_privacy == "private" or manifest_privacy == "private":
            return runtime_pool in {"trusted_runtime_pool", "enterprise_pool"}
        if request_privacy == "protected" or manifest_privacy == "protected":
            return runtime_pool in {"trusted_runtime_pool", "enterprise_pool", "large_gpu_pool"}
        return True
