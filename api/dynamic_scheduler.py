from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from api.sqlite_utils import connect_sqlite


class DynamicScheduler:
    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def reprioritize(self) -> dict[str, Any]:
        updated: list[dict[str, Any]] = []
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM jobs WHERE status = 'queued'").fetchall()
            for row in rows:
                job = dict(row)
                payload = json.loads(job["payload_json"])
                old_priority = int(payload.get("priority", 50))
                attempts = int(job.get("attempts", 0))
                priority = old_priority
                if payload.get("requires_gpu"):
                    priority += 15
                if job["job_type"] in {"verification", "evaluation", "evaluation_batch"}:
                    priority += 10
                if attempts > 0:
                    priority -= min(30, attempts * 5)
                priority = max(1, min(100, priority))
                if priority != old_priority:
                    payload["priority"] = priority
                    conn.execute("UPDATE jobs SET payload_json = ? WHERE job_id = ?", (json.dumps(payload, ensure_ascii=False), job["job_id"]))
                    updated.append({"job_id": job["job_id"], "old_priority": old_priority, "new_priority": priority})
        return {"updated": updated, "count": len(updated)}

    def preview(self, limit: int = 50) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute("SELECT job_id, job_type, payload_json, attempts, created_at FROM jobs WHERE status = 'queued' LIMIT ?", (limit,)).fetchall()
        jobs = []
        for row in rows:
            item = dict(row)
            payload = json.loads(item.pop("payload_json"))
            item["priority"] = payload.get("priority", 50)
            item["payload"] = payload
            jobs.append(item)
        jobs.sort(key=lambda item: item["priority"], reverse=True)
        return {"jobs": jobs}
