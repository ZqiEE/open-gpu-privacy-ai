from __future__ import annotations

import os

from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore
from api.owned_model_runtime import OwnedModelRequest, OwnedModelRuntime, OwnedModelUnavailable
from api.route_policy import check_route


class CheckedOwnedChatRequest(BaseModel):
    prompt: str
    user_id: str = "local"
    conversation_id: str | None = None
    model_id: str = "ailovanta-owned"
    version: str = "candidate"
    policy_mode: str = "open_research"


def checked_owned_chat(body: CheckedOwnedChatRequest, runtime_registry) -> dict:
    request_id = "owned-" + (body.conversation_id or body.user_id)
    model_key = f"{body.model_id}:{body.version}"
    policy = check_route(body.model_id, model_key, request_id, ArtifactBindingStore(os.getenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", "runtime_data/artifact_bindings.sqlite3")))
    if policy is not None:
        return {
            "ok": False,
            "answer": "Ailovanta owned model runtime is not ready: " + policy.get("reason", "route rejected"),
            "source": "owned-runtime-unavailable",
            "model_id": body.model_id,
            "version": body.version,
            "owned_model_ready": False,
            "route_policy": policy,
        }
    try:
        result = OwnedModelRuntime(runtime_registry).generate(
            OwnedModelRequest(
                prompt=body.prompt,
                model_id=body.model_id,
                version=body.version,
                policy_mode="open_research",
                user_id=body.user_id,
                conversation_id=body.conversation_id,
            )
        )
    except OwnedModelUnavailable as exc:
        return {
            "ok": False,
            "answer": "Ailovanta owned model runtime is not ready: " + str(exc),
            "source": "owned-runtime-unavailable",
            "model_id": body.model_id,
            "version": body.version,
            "owned_model_ready": False,
        }
    return {
        "ok": True,
        "answer": result.answer,
        "source": result.source,
        "model_id": result.model_id,
        "version": result.version,
        "runtime_route": result.runtime_route,
        "policy_mode": result.policy_mode,
        "owned_model_ready": True,
    }
