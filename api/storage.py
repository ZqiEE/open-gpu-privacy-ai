from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


class SchedulerStore:
    """SQLite-backed local scheduler store.

    v0.9 adds training jobs and a model version registry.
    The same API can later be backed by PostgreSQL and Redis.
    """

    def __init__(self, path: str | Path = "runtime_data/scheduler.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.seed_jobs()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    device_name TEXT NOT NULL,
                    cpu_threads INTEGER NOT NULL,
                    memory_gb REAL NOT NULL,
                    has_gpu INTEGER NOT NULL,
                    gpu_name TEXT,
                    contribution_percent INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    trust INTEGER NOT NULL DEFAULT 30,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    assigned_to TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    assigned_at TEXT,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS results (
                    result_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_summary TEXT NOT NULL,
                    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS verifications (
                    verification_id TEXT PRIMARY KEY,
                    result_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    passed INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS model_versions (
                    model_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_model TEXT NOT NULL,
                    source_job_id TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def seed_jobs(self) -> None:
        seeds = [
            ("job-rag-001", "rag_index", {"tokens": 1200}),
            ("job-eval-001", "evaluation", {"samples": 12}),
            ("job-lora-001", "lora_micro", {"steps": 20}),
            ("job-verify-001", "verification", {"samples": 6}),
        ]
        with self.connect() as conn:
            for job_id, job_type, payload in seeds:
                conn.execute("INSERT OR IGNORE INTO jobs (job_id, job_type, payload_json) VALUES (?, ?, ?)", (job_id, job_type, json.dumps(payload)))

    def enqueue_job(self, job_id: str, job_type: str, payload: dict) -> dict:
        with self.connect() as conn:
            conn.execute("INSERT INTO jobs (job_id, job_type, payload_json) VALUES (?, ?, ?)", (job_id, job_type, json.dumps(payload)))
        return self._api_job(self.get_job(job_id) or {})

    def list_jobs(self, status: str | None = None, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            if status:
                rows = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api_job(dict(row)) for row in rows]

    def register_node(self, body: dict[str, Any]) -> dict:
        node_id = "node_" + uuid4().hex[:12]
        score = body["cpu_threads"] * 8 + int(body["memory_gb"] * 10) + (60 if body.get("has_gpu") else 10)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO nodes (
                    node_id, device_name, cpu_threads, memory_gb, has_gpu, gpu_name,
                    contribution_percent, score, trust, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (node_id, body["device_name"], body["cpu_threads"], body["memory_gb"], 1 if body.get("has_gpu") else 0, body.get("gpu_name"), body.get("contribution_percent", 30), score, 30, "online"),
            )
        return self.get_node(node_id) or {}

    def get_node(self, node_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,)).fetchone()
        node = row_to_dict(row)
        if node:
            node["has_gpu"] = bool(node["has_gpu"])
        return node

    def update_heartbeat(self, node_id: str, status: str) -> dict | None:
        with self.connect() as conn:
            conn.execute("UPDATE nodes SET status = ?, last_seen = CURRENT_TIMESTAMP WHERE node_id = ?", (status, node_id))
        return self.get_node(node_id)

    def next_job(self, node_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE status = 'queued' ORDER BY attempts ASC, created_at ASC LIMIT 1").fetchone()
            if not row:
                return None
            conn.execute(
                "UPDATE jobs SET status = 'assigned', assigned_to = ?, assigned_at = CURRENT_TIMESTAMP, attempts = attempts + 1 WHERE job_id = ?",
                (node_id, row["job_id"]),
            )
        job = self.get_job(row["job_id"])
        return self._api_job(job) if job else None

    def get_job(self, job_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return row_to_dict(row)

    def submit_result(self, body: dict[str, Any]) -> dict:
        result_id = "result_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute("INSERT INTO results (result_id, node_id, job_id, status, output_summary) VALUES (?, ?, ?, ?, ?)", (result_id, body["node_id"], body["job_id"], body["status"], body["output_summary"]))
            conn.execute("UPDATE jobs SET status = ?, finished_at = CURRENT_TIMESTAMP WHERE job_id = ?", ("done" if body["status"] == "ok" else "failed", body["job_id"]))
            if body["status"] == "ok":
                conn.execute("UPDATE nodes SET trust = MIN(trust + 1, 100) WHERE node_id = ?", (body["node_id"],))
            else:
                conn.execute("UPDATE nodes SET trust = MAX(trust - 2, 0) WHERE node_id = ?", (body["node_id"],))
        return self.get_result(result_id) or {}

    def get_result(self, result_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM results WHERE result_id = ?", (result_id,)).fetchone()
        return row_to_dict(row)

    def record_verification(self, result: dict, score: float, passed: bool, reason: str) -> dict:
        verification_id = "verify_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO verifications (verification_id, result_id, job_id, node_id, score, passed, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (verification_id, result["result_id"], result["job_id"], result["node_id"], score, 1 if passed else 0, reason),
            )
            if passed:
                conn.execute("UPDATE nodes SET trust = MIN(trust + 1, 100) WHERE node_id = ?", (result["node_id"],))
            else:
                conn.execute("UPDATE nodes SET trust = MAX(trust - 3, 0) WHERE node_id = ?", (result["node_id"],))
        return self.get_verification(verification_id) or {}

    def get_verification(self, verification_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM verifications WHERE verification_id = ?", (verification_id,)).fetchone()
        item = row_to_dict(row)
        if item:
            item["passed"] = bool(item["passed"])
        return item

    def register_model_version(self, record: dict) -> dict:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO model_versions (model_id, name, base_model, source_job_id, notes) VALUES (?, ?, ?, ?, ?)",
                (record["model_id"], record["name"], record["base_model"], record["source_job_id"], record.get("notes", "")),
            )
        return self.get_model_version(record["model_id"]) or {}

    def get_model_version(self, model_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM model_versions WHERE model_id = ?", (model_id,)).fetchone()
        return row_to_dict(row)

    def list_model_versions(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM model_versions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

    def retry_failed_jobs(self, max_attempts: int = 3) -> dict:
        with self.connect() as conn:
            cur = conn.execute("UPDATE jobs SET status = 'queued', assigned_to = NULL, assigned_at = NULL, finished_at = NULL WHERE status = 'failed' AND attempts < ?", (max_attempts,))
        return {"requeued_failed_jobs": cur.rowcount, "max_attempts": max_attempts}

    def requeue_stale_assigned(self, older_than_minutes: int = 30) -> dict:
        with self.connect() as conn:
            cur = conn.execute(
                """
                UPDATE jobs
                SET status = 'queued', assigned_to = NULL, assigned_at = NULL
                WHERE status = 'assigned'
                AND assigned_at IS NOT NULL
                AND assigned_at < datetime('now', ?)
                """,
                (f"-{older_than_minutes} minutes",),
            )
        return {"requeued_stale_jobs": cur.rowcount, "older_than_minutes": older_than_minutes}

    def status(self) -> dict:
        with self.connect() as conn:
            nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            queued = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'queued'").fetchone()[0]
            assigned = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'assigned'").fetchone()[0]
            done = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'done'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'failed'").fetchone()[0]
            results = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
            verifications = conn.execute("SELECT COUNT(*) FROM verifications").fetchone()[0]
            passed = conn.execute("SELECT COUNT(*) FROM verifications WHERE passed = 1").fetchone()[0]
            model_versions = conn.execute("SELECT COUNT(*) FROM model_versions").fetchone()[0]
        return {"nodes": nodes, "queued_jobs": queued, "assigned_jobs": assigned, "done_jobs": done, "failed_jobs": failed, "submitted_results": results, "verifications": verifications, "passed_verifications": passed, "model_versions": model_versions, "store": "sqlite", "path": str(self.path)}

    @staticmethod
    def _api_job(job: dict) -> dict:
        return {
            "id": job["job_id"],
            "type": job["job_type"],
            "payload": json.loads(job["payload_json"]),
            "status": job.get("status"),
            "assigned_to": job.get("assigned_to"),
            "assigned_at": job.get("assigned_at"),
            "attempts": job.get("attempts", 0),
        }
