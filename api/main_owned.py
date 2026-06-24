from __future__ import annotations

from pydantic import BaseModel

from api.chain_registry_api import router as chain_registry_router
from api.core_result_api import router as core_result_router
from api.data_rights_api import router as data_rights_router
from api.main import app, conversations, runtime_registry, usage_store
from api.owned_model_runtime import OwnedModelRequest, OwnedModelRuntime, OwnedModelUnavailable

app.include_router(data_rights_router)
app.include_router(core_result_router)
app.include_router(chain_registry_router)


class OwnedChatRequest(BaseModel):
    prompt: str
    user_id: str = "local"
    conversation_id: str | None = None
    title: str = "Owned model chat"
    model_id: str = "ailovanta-owned"
    version: str = "candidate"
    policy_mode: str = "open_research"


@app.post("/ailovanta/v1/owned-chat")
def ailovanta_owned_chat(body: OwnedChatRequest) -> dict:
    convo = conversations.get_or_create(body.conversation_id, body.user_id, body.title)
    conversations.add_message(convo["id"], "user", body.prompt, source="user", model_id=body.model_id)

    owned_runtime = OwnedModelRuntime(runtime_registry)
    try:
        result = owned_runtime.generate(
            OwnedModelRequest(
                prompt=body.prompt,
                model_id=body.model_id,
                version=body.version,
                policy_mode="open_research",
                user_id=body.user_id,
                conversation_id=convo["id"],
            )
        )
    except OwnedModelUnavailable as exc:
        answer = "Ailovanta owned model runtime is not ready: " + str(exc)
        conversations.add_message(convo["id"], "assistant", answer, source="owned-runtime-unavailable", model_id=body.model_id)
        return {
            "ok": False,
            "conversation_id": convo["id"],
            "answer": answer,
            "source": "owned-runtime-unavailable",
            "model_id": body.model_id,
            "version": body.version,
            "owned_model_ready": False,
        }

    conversations.add_message(convo["id"], "assistant", result.answer, source=result.source, model_id=result.model_id)
    usage_store.record(body.user_id, "ailovanta.owned_chat", 1, result.source, {"conversation_id": convo["id"], "model_id": result.model_id, "version": result.version})
    return {
        "ok": True,
        "conversation_id": convo["id"],
        "answer": result.answer,
        "source": result.source,
        "model_id": result.model_id,
        "version": result.version,
        "runtime_route": result.runtime_route,
        "policy_mode": result.policy_mode,
        "owned_model_ready": True,
    }
