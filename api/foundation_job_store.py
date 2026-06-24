from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite

FOUNDATION_JOB_SCHEMA = "ailovanta.foundation_job.v1"


class FoundationJobStore:
    def __init__(self, path: str | Path = "runtime_data/foundation_jobs.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS foundation_jobs (
                    job_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    target_version TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def create(self, payload: dict[str, Any]) -> dict:
        self._validate_payload(payload)
        job_id = payload.get("job_id") or "foundation_job_" + uuid4().hex[:12]
        payload = {**payload, "job_id": job_id, "schema_version": FOUNDATION_JOB_SCHEMA}
        model = payload["model"]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO foundation_jobs (
                    job_id, model_id, target_version, stage, status, payload_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    job_id,
                    model.get("model_id", "ailovanta-owned"),
                    model.get("target_version", "candidate"),
                    payload.get("stage", "pretrain"),
                    payload.get("status", "queued"),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
        return self.get(job_id) or {}

    def get(self, job_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM foundation_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._api_job(dict(row)) if row else None

    def list_jobs(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM foundation_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api_job(dict(row)) for row in rows]

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        for key in ["model", "dataset_shards", "nodes"]:
            if not payload.get(key):
                raise ValueError(f"missing required field: {key}")
        if not isinstance(payload["dataset_shards"], list) or not payload["dataset_shards"]:
            raise ValueError("dataset_shards must be a non-empty list")
        if not isinstance(payload["nodes"], list) or not payload["nodes"]:
            raise ValueError("nodes must be a non-empty list")

    @staticmethod
    def _api_job(row: dict) -> dict:
        row["payload"] = json.loads(row.pop("payload_json") or "{}")
        return row
