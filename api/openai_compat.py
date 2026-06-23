from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "ailovanta-local"
    messages: list[ChatMessage]
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)
    stream: bool = False
    user: str | None = None


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def extract_user_prompt(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user" and message.content.strip():
            return message.content
    return ""


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def build_chat_completion_response(model: str, answer: str, prompt_text: str) -> dict:
    prompt_tokens = estimate_tokens(prompt_text)
    completion_tokens = estimate_tokens(answer)
    return {
        "id": f"chatcmpl_ailovanta_{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            ChatCompletionChoice(message=ChatMessage(role="assistant", content=answer)).model_dump()
        ],
        "usage": ChatCompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ).model_dump(),
    }
