from __future__ import annotations

from dataclasses import dataclass, asdict
from time import time


STARTED_AT = time()


@dataclass
class HealthStatus:
    ok: bool
    service: str
    version: str
    uptime_seconds: float


def get_health(version: str) -> dict:
    return asdict(
        HealthStatus(
            ok=True,
            service="ailovanta-api",
            version=version,
            uptime_seconds=round(time() - STARTED_AT, 3),
        )
    )
