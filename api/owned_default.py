from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from api.owned_entry import CheckedOwnedChatRequest, checked_owned_chat
from api.route_book import RouteBook


class DefaultOwnedChatRequest(BaseModel):
    prompt: str
    user_id: str = "local"
    conversation_id: str | None = None
    route_key: str = "owned-chat/default"
    policy_mode: str = "open_research"


def split_model_key(model_key: str) -> tuple[str, str]:
    if ":" not in model_key:
        return model_key, "candidate"
    model_id, version = model_key.split(":", 1)
    return model_id, version


def default_owned_chat(body: DefaultOwnedChatRequest, runtime_registry) -> dict[str, Any]:
    route = RouteBook().active(body.route_key)
    if not route:
        return {
            "ok": False,
            "answer": "Ailovanta owned model route is not active: " + body.route_key,
            "source": "owned-route-unavailable",
            "owned_model_ready": False,
            "route_key": body.route_key,
            "route": None,
        }
    model_id, version = split_model_key(str(route["model_key"]))
    result = checked_owned_chat(
        CheckedOwnedChatRequest(
            prompt=body.prompt,
            user_id=body.user_id,
            conversation_id=body.conversation_id,
            model_id=model_id,
            version=version,
            policy_mode=body.policy_mode,
        ),
        runtime_registry,
    )
    return {**result, "route_key": body.route_key, "active_route": route}
