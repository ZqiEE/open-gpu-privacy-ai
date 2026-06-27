from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CodeChatRequest(BaseModel):
    prompt: str
    user_id: str = "local"


@router.post("/ailovanta/v1/code-chat")
def code_chat(body: CodeChatRequest) -> dict:
    return {"answer": "Ailovanta-Code endpoint is ready.", "prompt": body.prompt, "user_id": body.user_id, "source": "code-chat"}
