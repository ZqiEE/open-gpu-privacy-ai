from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from typing import Literal

from api.artifact_binding import ArtifactBindingStore
from api.runtime_ref import check_runtime_ref
from api.worker_transport import WorkerInferenceClient, WorkerInferenceRequest, WorkerInferenceUnavailable


PolicyMode = Literal["standard", "open_research"]


@dataclass(frozen=True)
class OwnedModelRequest:
    prompt: str
    model_id: str = "ailovanta-owned"
    version: str = "candidate"
    policy_mode: PolicyMode = "open_research"
    user_id: str = "local"
    conversation_id: str | None = None


@dataclass(frozen=True)
class OwnedModelResult:
    answer: str
    source: str
    model_id: str
    version: str
    runtime_route: dict
    policy_mode: PolicyMode
    worker_result: dict[str, Any]


class OwnedModelUnavailable(RuntimeError):
    pass


class OwnedModelRuntime:
    def __init__(self, runtime_registry, worker_client: WorkerInferenceClient | None = None, binding_store: ArtifactBindingStore | None = None) -> None:
        self.runtime_registry = runtime_registry
        self.worker_client = worker_client or WorkerInferenceClient()
        self.binding_store = binding_store or ArtifactBindingStore(os.getenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", "runtime_data/artifact_bindings.sqlite3"))

    def route(self, request: OwnedModelRequest) -> dict:
        from api.runtime_router import RuntimeRequest

        return self.runtime_registry.route(
            RuntimeRequest(
                request_id=f"owned-{request.conversation_id or request.user_id}",
                model_id=request.model_id,
                version=request.version,
                task_type="chat_completion",
                privacy_level="protected",
                latency_target_ms=2000,
                max_price_per_1k_tokens=0.1,
                region_hint="auto",
                verification_required=True,
            )
        )

    def active_binding(self, request: OwnedModelRequest) -> dict | None:
        return self.binding_store.latest_for_model(f"{request.model_id}:{request.version}", active_only=True)

    def assert_binding_usable(self, request: OwnedModelRequest) -> dict | None:
        binding = self.active_binding(request)
        if not binding:
            return None
        report = check_runtime_ref(binding)
        if not report.get("ready"):
            raise OwnedModelUnavailable("artifact binding is not locally reachable: " + str(report.get("reason")))
        return binding

    def generate(self, request: OwnedModelRequest) -> OwnedModelResult:
        binding = self.assert_binding_usable(request)
        route = self.route(request)
        if not route.get("assigned"):
            raise OwnedModelUnavailable("no verified Ailovanta runtime manifest is available")

        assignment = route.get("assignment") or {}
        manifest_hash = assignment.get("model_manifest_hash")
        runtime_id = assignment.get("runtime_id")
        node_id = assignment.get("node_id")
        if not manifest_hash:
            raise OwnedModelUnavailable("assigned runtime has no model manifest hash")
        if not runtime_id or not node_id:
            raise OwnedModelUnavailable("assigned runtime is missing runtime_id or node_id")

        try:
            worker_result = self.worker_client.infer(
                WorkerInferenceRequest(
                    prompt=request.prompt,
                    model_id=request.model_id,
                    version=request.version,
                    policy_mode=request.policy_mode,
                    runtime_id=runtime_id,
                    node_id=node_id,
                    model_manifest_hash=manifest_hash,
                )
            )
        except WorkerInferenceUnavailable as exc:
            raise OwnedModelUnavailable(f"worker inference unavailable: {exc}") from exc

        route_with_binding = {**route, "artifact_binding_id": binding.get("binding_id") if binding else None}
        return OwnedModelResult(
            answer=worker_result.answer,
            source=worker_result.source,
            model_id=request.model_id,
            version=request.version,
            runtime_route=route_with_binding,
            policy_mode=request.policy_mode,
            worker_result=worker_result.raw,
        )
