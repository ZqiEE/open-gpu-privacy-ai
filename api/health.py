from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from time import time


STARTED_AT = time()


@dataclass
class HealthStatus:
    ok: bool
    service: str
    version: str
    uptime_seconds: float
    local_model: dict


def local_model_status() -> dict:
    return {
        "mode": "ollama_configured",
        "adapter": "ollama",
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "fallback": "Ailovanta will use local fallback text if Ollama is not reachable.",
    }


def get_health(version: str) -> dict:
    return asdict(
        HealthStatus(
            ok=True,
            service="ailovanta-api",
            version=version,
            uptime_seconds=round(time() - STARTED_AT, 3),
            local_model=local_model_status(),
        )
    )
