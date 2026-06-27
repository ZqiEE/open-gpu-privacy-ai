from __future__ import annotations

from fastapi import APIRouter

from api.owned_ready_probe import check_owned_chat_default


router = APIRouter(prefix="/ops/default-chat", tags=["default-chat"])


@router.get("/ready")
def default_chat_ready(route_key: str = "owned-chat/default") -> dict:
    return check_owned_chat_default(route_key)
