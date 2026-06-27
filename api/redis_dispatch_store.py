from __future__ import annotations

import json
import os
from typing import Any

from api.task_router import TaskRouter


class RedisDispatchStore:
    def __init__(self, base_store: Any, redis_url: str | None = None, prefix: str = "ailovanta") -> None:
        self.base = base_store
        self.prefix = prefix
        self.router = TaskRouter()
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "")
        self.client = None
        if self.redis_url:
            try:
                import redis  # type: ignore
                self.client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            except Exception:
                self.client = None

    def enabled(self) -> bool:
        return self.client is not None

    def queue_key(self) -> str:
        return f"{self.prefix}:jobs:queued"

    def enqueue_job(self, job_id: str, job_type: str, payload: dict) -> dict:
        job = self.base.enqueue_job(job_id, job_type, payload)
        if self.client:
            priority = int(payload.get("priority", 50))
            self.client.zadd(self.queue_key(), {job_id: priority})
        return job

    def next_job(self, node_id: str) -> dict | None:
        if not self.client:
            return self.base.next_job(node_id)
        node = self.base.get_node(node_id)
        if not node:
            return None
        candidates = self.client.zrevrange(self.queue_key(), 0, 49)
        for job_id in candidates:
            raw = self.base.get_job(job_id)
            if not raw:
                self.client.zrem(self.queue_key(), job_id)
                continue
            api_job = self.base._api_job(raw) if hasattr(self.base, "_api_job") else raw
            candidate = {"job_id": api_job["id"], "job_type": api_job["type"], "payload_json": json.dumps(api_job["payload"]), "attempts": api_job.get("attempts", 0)}
            if not self.router.can_assign(node, candidate)[0]:
                continue
            self.client.zrem(self.queue_key(), job_id)
            if hasattr(self.base, "claim_job"):
                claimed = self.base.claim_job(job_id, node_id)
                if claimed:
                    return claimed
            return self.base.next_job(node_id)
        return None

    def redis_status(self) -> dict[str, Any]:
        if not self.client:
            return {"enabled": False}
        try:
            return {"enabled": True, "queued": self.client.zcard(self.queue_key()), "ok": bool(self.client.ping())}
        except Exception as exc:
            return {"enabled": True, "ok": False, "error": str(exc)}

    def __getattr__(self, name: str) -> Any:
        return getattr(self.base, name)
