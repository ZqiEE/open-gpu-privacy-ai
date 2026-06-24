from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.runtime_router import ModelManifest
from api.runtime_store import RuntimeStore
from api.sqlite_utils import connect_sqlite

CORE_RESULT_SCHEMA = "ailovanta.core_result.v1"


class CoreResultStore:
    """Stores core training result manifests and promotes candidates to runtime models."""

    def __init__(self, path: str | Path = "runtime_data/core_results.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS core_results (
                    result_id TEXT PRIMARY KEY,
                    source_job_id TEXT NOT NULL,
                    round_id TEXT NOT NULL,
                    next_model_version TEXT NOT NULL,
                    base_model TEXT NOT NULL,
                    dataset_uri TEXT NOT NULL,
                    accepted_candidates INTEGER NOT NULL,
                    promotion_status TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def register_manifest(self, manifest: dict[str, Any]) -> dict:
        self._validate_manifest(manifest)
        result_id = manifest.get("result_id") or "core_result_" + uuid4().hex[:12]
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO core_results (
                    result_id, source_job_id, round_id, next_model_version, base_model,
                    dataset_uri, accepted_candidates, promotion_status, manifest_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    manifest["source_job_id"],
                    manifest["round_id"],
                    manifest["next_model_version"],
                    manifest.get("base_model", ""),
                    manifest.get("dataset_uri", ""),
                    int(manifest.get("accepted_candidates") or 0),
                    manifest.get("promotion_status", "candidate"),
                    json.dumps(manifest, ensure_ascii=False),
                ),
            )
        return self.get(result_id) or {}

    def get(self, result_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM core_results WHERE result_id = ?", (result_id,)).fetchone()
        return self._api_result(dict(row)) if row else None

    def list_results(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM core_results ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api_result(dict(row)) for row in rows]

    def promote_to_runtime(
        self,
        result_id: str,
        runtime_store: RuntimeStore,
        model_id: str = "ailovanta-owned",
        privacy_level: str = "protected",
        min_gpu_memory_gb: float = 8.0,
    ) -> dict:
        result = self.get(result_id)
        if not result:
            raise ValueError("core result not found")
        if result["promotion_status"] not in {"candidate", "promoted"}:
            raise ValueError("core result is not promotable")
        if int(result["accepted_candidates"]) <= 0:
            raise ValueError("core result has no accepted candidates")

        model = runtime_store.register_model(
            ModelManifest(
                model_id=model_id,
                version=result["next_model_version"],
                manifest_hash=self._manifest_hash(result),
                privacy_level=privacy_level,
                min_gpu_memory_gb=min_gpu_memory_gb,
                allowed_pools=["trusted_runtime_pool", "enterprise_pool"],
                quantization="candidate",
                context_length=8192,
                adapter_compatible=True,
                status="active",
            )
        )
        return {"ok": True, "core_result": result, "runtime_model": model}

    @staticmethod
    def _validate_manifest(manifest: dict[str, Any]) -> None:
        if manifest.get("schema_version") != CORE_RESULT_SCHEMA:
            raise ValueError("unsupported core result schema")
        for key in ["source_job_id", "round_id", "next_model_version"]:
            if not manifest.get(key):
                raise ValueError(f"missing required field: {key}")

    @staticmethod
    def _manifest_hash(result: dict) -> str:
        artifact = result.get("manifest", {}).get("artifact") or {}
        if artifact.get("artifact_hash"):
            return str(artifact["artifact_hash"])
        raw = json.dumps(result["manifest"], ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _api_result(row: dict) -> dict:
        row["manifest"] = json.loads(row.pop("manifest_json") or "{}")
        return row
