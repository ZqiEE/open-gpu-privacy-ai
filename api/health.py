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
        "mode": os.getenv("AILOVANTA_MODEL_STAGE", "bootstrap_local_runtime"),
        "adapter": "ollama",
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        "owned_model_ready": os.getenv("AILOVANTA_OWNED_MODEL_READY", "false").lower() == "true",
        "ownership_boundary": "Current chat inference uses a local bootstrap model. It is not Alibaba Cloud, DashScope, or a production Ailovanta-owned model.",
        "target_backend": "Ailovanta-owned inference begins after the public/core bridge can promote verified training artifacts into runtime model manifests.",
        "fallback": "Ailovanta will use local fallback text if the bootstrap runtime is not reachable.",
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
