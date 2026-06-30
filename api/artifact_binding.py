from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.sqlite_utils import connect_sqlite

BINDING_SCHEMA = "ailovanta.artifact_runtime_binding.v1"


class ArtifactBindingStore:
    def __init__(self, path: str | Path = "runtime_data/artifact_bindings.sqlite3") -> None:
        self.raw_path = str(path)
        self.path = Path(path)
        self._memory_conn: sqlite3.Connection | None = None
        if self.raw_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS artifact_bindings (
                    binding_id TEXT PRIMARY KEY,
                    model_key TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    runtime_manifest_hash TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    checkpoint_uri TEXT NOT NULL,
                    backend_kind TEXT NOT NULL,
                    backend_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_artifact_bindings_model_key ON artifact_bindings(model_key);
                CREATE INDEX IF NOT EXISTS idx_artifact_bindings_artifact_hash ON artifact_bindings(artifact_hash);
                CREATE INDEX IF NOT EXISTS idx_artifact_bindings_status ON artifact_bindings(status);
                """
            )

    def register_binding(
        self,
        runtime_model: dict[str, Any],
        artifact: dict[str, Any],
        backend_kind: str = "checkpoint-artifact",
        backend_ref: str | None = None,
        status: str = "candidate",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        model_key = runtime_model.get("model_key") or f"{runtime_model['model_id']}:{runtime_model['version']}"
        artifact_hash = artifact["artifact_hash"]
        binding_id = "binding_" + uuid4().hex[:12]
        payload = {
            "schema_version": BINDING_SCHEMA,
            "binding_id": binding_id,
            "model_key": model_key,
            "model_id": runtime_model["model_id"],
            "version": runtime_model["version"],
            "runtime_manifest_hash": runtime_model["manifest_hash"],
            "artifact_hash": artifact_hash,
            "artifact_id": artifact.get("artifact_id", ""),
            "checkpoint_uri": artifact.get("checkpoint_uri", ""),
            "backend_kind": backend_kind,
            "backend_ref": backend_ref or artifact.get("checkpoint_uri", ""),
            "status": status,
            "metadata": metadata or {},
        }
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO artifact_bindings (
                    binding_id, model_key, model_id, version, runtime_manifest_hash,
                    artifact_hash, artifact_id, checkpoint_uri, backend_kind, backend_ref,
                    status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["binding_id"],
                    payload["model_key"],
                    payload["model_id"],
                    payload["version"],
                    payload["runtime_manifest_hash"],
                    payload["artifact_hash"],
                    payload["artifact_id"],
                    payload["checkpoint_uri"],
                    payload["backend_kind"],
                    payload["backend_ref"],
                    payload["status"],
                    json.dumps(payload["metadata"], ensure_ascii=False),
                ),
            )
        return self.get(binding_id) or {}

    def get(self, binding_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM artifact_bindings WHERE binding_id = ?", (binding_id,)).fetchone()
        return self._api_row(dict(row)) if row else None

    def latest_for_model(self, model_key: str, active_only: bool = False) -> dict[str, Any] | None:
        query = "SELECT * FROM artifact_bindings WHERE model_key = ?"
        params: list[Any] = [model_key]
        if active_only:
            query += " AND status IN ('active', 'candidate')"
        query += " ORDER BY created_at DESC LIMIT 1"
        with self.connect() as conn:
            row = conn.execute(query, params).fetchone()
        return self._api_row(dict(row)) if row else None

    def latest_for_model_statuses(self, model_key: str, statuses: list[str] | tuple[str, ...]) -> dict[str, Any] | None:
        if not statuses:
            return None
        placeholders = ",".join("?" for _ in statuses)
        query = f"SELECT * FROM artifact_bindings WHERE model_key = ? AND status IN ({placeholders}) ORDER BY created_at DESC LIMIT 1"
        params: list[Any] = [model_key, *statuses]
        with self.connect() as conn:
            row = conn.execute(query, params).fetchone()
        return self._api_row(dict(row)) if row else None

    def list_bindings(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM artifact_bindings ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api_row(dict(row)) for row in rows]

    def set_status(self, binding_id: str, status: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("UPDATE artifact_bindings SET status = ? WHERE binding_id = ?", (status, binding_id))
        return self.get(binding_id)

    def update_metadata(self, binding_id: str, metadata: dict[str, Any]) -> dict[str, Any] | None:
        with self.connect() as conn:
            conn.execute("UPDATE artifact_bindings SET metadata_json = ? WHERE binding_id = ?", (json.dumps(metadata, ensure_ascii=False), binding_id))
        return self.get(binding_id)

    @staticmethod
    def _api_row(row: dict[str, Any]) -> dict[str, Any]:
        row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        row["schema_version"] = BINDING_SCHEMA
        return row
