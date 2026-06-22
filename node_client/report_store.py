from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class ReportStore:
    def __init__(self, path: str | Path = "runtime_data/worker_reports.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS worker_reports (
                    report_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    job_id TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    runtime_seconds REAL NOT NULL,
                    policy_reason TEXT NOT NULL,
                    descriptor_ok INTEGER NOT NULL,
                    descriptor_reason TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )

    def save(self, report: dict[str, Any]) -> dict:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO worker_reports (
                    report_id, node_id, job_id, job_type, status, runtime_seconds,
                    policy_reason, descriptor_ok, descriptor_reason, report_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report["report_id"],
                    report["node_id"],
                    report["job_id"],
                    report["job_type"],
                    report["status"],
                    report["runtime_seconds"],
                    report["policy_reason"],
                    1 if report.get("descriptor_ok") else 0,
                    report["descriptor_reason"],
                    json.dumps(report, ensure_ascii=False),
                    report["created_at"],
                ),
            )
        return self.get(report["report_id"]) or {}

    def get(self, report_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM worker_reports WHERE report_id = ?", (report_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["descriptor_ok"] = bool(data["descriptor_ok"])
        return data

    def list_reports(self, node_id: str | None = None, status: str | None = None, limit: int = 100) -> list[dict]:
        query = "SELECT * FROM worker_reports"
        args: list[Any] = []
        clauses: list[str] = []
        if node_id:
            clauses.append("node_id = ?")
            args.append(node_id)
        if status:
            clauses.append("status = ?")
            args.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        with self.connect() as conn:
            rows = conn.execute(query, args).fetchall()
        reports = []
        for row in rows:
            item = dict(row)
            item["descriptor_ok"] = bool(item["descriptor_ok"])
            reports.append(item)
        return reports

    def summary(self) -> dict:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM worker_reports").fetchone()[0]
            ok = conn.execute("SELECT COUNT(*) FROM worker_reports WHERE status = 'ok'").fetchone()[0]
            failed = conn.execute("SELECT COUNT(*) FROM worker_reports WHERE status = 'failed'").fetchone()[0]
            nodes = conn.execute("SELECT COUNT(DISTINCT node_id) FROM worker_reports").fetchone()[0]
        return {"total_reports": total, "ok_reports": ok, "failed_reports": failed, "nodes": nodes}
