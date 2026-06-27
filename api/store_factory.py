from __future__ import annotations

import os
from typing import Any

from api.postgres_store import PostgresStore
from api.redis_dispatch_store import RedisDispatchStore
from api.storage import SchedulerStore


def create_scheduler_store() -> Any:
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith(("postgresql://", "postgres://")):
        base = PostgresStore(database_url)
    else:
        base = SchedulerStore()
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        return RedisDispatchStore(base, redis_url)
    return base


def store_status(store: Any) -> dict:
    status = store.status()
    if hasattr(store, "redis_status"):
        status["redis"] = store.redis_status()
    return status
