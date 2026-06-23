from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field


class AilovantaRunRequest(BaseModel):
    prompt: str
    model_id: str = "ailovanta-local"
    version: str = "local"
    task_type: Literal["chat_completion", "embedding", "rerank", "batch", "training", "validation"] = "chat_completion"
    privacy_level: Literal["public", "protected", "private"] = "public"
    user_id: str = "local"
    region_hint: str = "auto"
    latency_target_ms: int = Field(default=2000, ge=1)
    max_price_per_1k_tokens: float = Field(default=0.1, ge=0)
    use_runtime_router: bool = True
    verification_required: bool = True


class AilovantaRunResult(BaseModel):
    id: str
    object: str = "ailovanta.run"
    created: int
    model_id: str
    version: str
    task_type: str
    answer: str
    source: str
    runtime_route: dict
    usage: dict


def token_estimate(text: str) -> int:
    return max(1, len(text) // 4)


def build_run_result(request: AilovantaRunRequest, answer: str, source: str, route: dict) -> dict:
    prompt_tokens = token_estimate(request.prompt)
    output_tokens = token_estimate(answer)
    return AilovantaRunResult(
        id=f"run_ailovanta_{int(time.time() * 1000)}",
        created=int(time.time()),
        model_id=request.model_id,
        version=request.version,
        task_type=request.task_type,
        answer=answer,
        source=source,
        runtime_route=route,
        usage={
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": prompt_tokens + output_tokens,
        },
    ).model_dump()
