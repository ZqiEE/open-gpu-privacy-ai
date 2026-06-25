from __future__ import annotations

from api.main_owned import app
from api.main import conversations, runtime_registry, usage_store
from api.owned_entry import CheckedOwnedChatRequest, checked_owned_chat


@app.post("/ailovanta/v1/owned-chat-checked")
def ailovanta_owned_chat_checked(body: CheckedOwnedChatRequest) -> dict:
    convo = conversations.get_or_create(body.conversation_id, body.user_id, "Owned model chat")
    conversations.add_message(convo["id"], "user", body.prompt, source="user", model_id=body.model_id)
    result = checked_owned_chat(
        CheckedOwnedChatRequest(
            prompt=body.prompt,
            user_id=body.user_id,
            conversation_id=convo["id"],
            model_id=body.model_id,
            version=body.version,
            policy_mode=body.policy_mode,
        ),
        runtime_registry,
    )
    conversations.add_message(convo["id"], "assistant", result["answer"], source=result["source"], model_id=body.model_id)
    if result.get("ok"):
        usage_store.record(body.user_id, "ailovanta.owned_chat_checked", 1, result["source"], {"conversation_id": convo["id"], "model_id": body.model_id, "version": body.version})
    return {**result, "conversation_id": convo["id"]}
