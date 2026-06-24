from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


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


class OwnedModelUnavailable(RuntimeError):
    pass


class OwnedModelRuntime:
    """Ailovanta-owned model runtime boundary.

    This class does not pretend that a third-party bootstrap model is the final
    Ailovanta model. It only allows an answer when the runtime router returns a
    verified Ailovanta runtime manifest.
    """

    def __init__(self, runtime_registry) -> None:
        self.runtime_registry = runtime_registry

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

    def generate(self, request: OwnedModelRequest) -> OwnedModelResult:
        route = self.route(request)
        if not route.get("assigned"):
            raise OwnedModelUnavailable("no verified Ailovanta runtime manifest is available")

        assignment = route.get("assignment") or {}
        manifest_hash = assignment.get("model_manifest_hash")
        if not manifest_hash:
            raise OwnedModelUnavailable("assigned runtime has no model manifest hash")

        return OwnedModelResult(
            answer=(
                "Ailovanta owned-model runtime is selected. "
                "Inference handoff is ready for the verified runtime worker. "
                "Next implementation step: attach the worker inference transport."
            ),
            source="ailovanta-owned-runtime",
            model_id=request.model_id,
            version=request.version,
            runtime_route=route,
            policy_mode=request.policy_mode,
        )
