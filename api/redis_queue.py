from __future__ import annotations

import json
import os
from typing import Any


class RedisQueue:
    def __init__(self, url: str | None = None, prefix: str = "ailovanta") -> None:
        self.url = url or os.environ.get("REDIS_URL", "")
        self.prefix = prefix
        self.client = None
        if self.url:
            try:
                import redis  # type: ignore
                self.client = redis.Redis.from_url(self.url, decode_responses=True)
            except Exception:
                self.client = None

    def enabled(self) -> bool:
        return self.client is not None

    def health(self) -> dict[str, Any]:
        if not self.client:
            return {"enabled": False, "ok": False, "reason": "redis not configured or dependency missing"}
        try:
            pong = self.client.ping()
            return {"enabled": True, "ok": bool(pong)}
        except Exception as exc:
            return {"enabled": True, "ok": False, "reason": str(exc)}

    def push_job(self, job: dict[str, Any], queue: str = "jobs") -> dict[str, Any]:
        if not self.client:
            return {"ok": False, "reason": "redis disabled"}
        key = f"{self.prefix}:{queue}"
        self.client.lpush(key, json.dumps(job, ensure_ascii=False))
        return {"ok": True, "queue": key, "length": self.client.llen(key)}

    def pop_job(self, queue: str = "jobs", timeout: int = 1) -> dict[str, Any] | None:
        if not self.client:
            return None
        key = f"{self.prefix}:{queue}"
        item = self.client.brpop(key, timeout=timeout)
        if not item:
            return None
        _key, raw = item
        return json.loads(raw)

    def stats(self) -> dict[str, Any]:
        if not self.client:
            return {"enabled": False}
        keys = [f"{self.prefix}:jobs", f"{self.prefix}:priority", f"{self.prefix}:deadletter"]
        return {"enabled": True, "queues": {key: self.client.llen(key) for key in keys}}
