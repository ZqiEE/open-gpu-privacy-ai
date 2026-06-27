from __future__ import annotations

import os
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from time import time

from fastapi import Request
from fastapi.responses import JSONResponse


DEFAULT_LIMITED_PREFIXES = (
    "/ailovanta/v1/",
    "/runtime/forward",
    "/wio/",
    "/catalog/",
    "/artifacts/",
    "/objects/",
    "/node-keys/",
    "/ops/",
)


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> tuple[bool, int, float]:
        now = time()
        bucket = self.events[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            retry_after = max(1.0, self.window_seconds - (now - bucket[0])) if bucket else float(self.window_seconds)
            return False, 0, retry_after
        bucket.append(now)
        return True, max(0, self.limit - len(bucket)), 0.0


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def client_key(request: Request) -> str:
    token = request.headers.get("X-Ailovanta-Client-Id") or request.headers.get("X-Ailovanta-Node-Id")
    if token:
        return token[:128]
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def limited_path(path: str, prefixes: tuple[str, ...] = DEFAULT_LIMITED_PREFIXES) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def install_rate_limit(app) -> None:
    enabled = bool_env("AILOVANTA_RATE_LIMIT_ENABLED", False)
    limit = int(os.getenv("AILOVANTA_RATE_LIMIT_PER_MINUTE", "120"))
    window = int(os.getenv("AILOVANTA_RATE_LIMIT_WINDOW_SECONDS", "60"))
    limiter = SlidingWindowLimiter(limit=max(1, limit), window_seconds=max(1, window))

    @app.middleware("http")
    async def rate_limit_guard(request: Request, call_next: Callable[[Request], Awaitable]):
        if not enabled or not limited_path(request.url.path):
            return await call_next(request)
        key = client_key(request) + ":" + request.url.path
        ok, remaining, retry_after = limiter.allow(key)
        if not ok:
            return JSONResponse(
                {"detail": "rate limit exceeded", "retry_after_seconds": round(retry_after, 3)},
                status_code=429,
                headers={"Retry-After": str(int(retry_after)), "X-RateLimit-Remaining": "0"},
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
