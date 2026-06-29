from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.reputation_ops import ReputationOps
from api.sqlite_utils import connect_sqlite

WORKER_RESULT_VALIDATION_SCHEMA = "ailovanta.worker_result_validation.v1"


class WorkerResultValidationStore:
    def __init__(self, path: str | Path = "runtime_data/worker_result_validations.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS worker_result_validations (
                    receipt_id TEXT PRIMARY KEY,
                    result_hash TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    runtime_id TEXT NOT NULL,
                    model_manifest_hash TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    score REAL NOT NULL,
                    blockers_json TEXT NOT NULL,
                    sampled_chunks_json TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_worker_result_validations_node ON worker_result_validations(node_id);
                CREATE INDEX IF NOT EXISTS idx_worker_result_validations_result_hash ON worker_result_validations(result_hash);
                """
            )

    def add(self, receipt: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO worker_result_validations (
                    receipt_id, result_hash, node_id, runtime_id, model_manifest_hash,
                    artifact_hash, passed, score, blockers_json, sampled_chunks_json, receipt_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt["receipt_id"],
                    receipt["result_hash"],
                    receipt["node_id"],
                    receipt["runtime_id"],
                    receipt["model_manifest_hash"],
                    receipt.get("artifact_hash") or "",
                    1 if receipt["passed"] else 0,
                    receipt["score"],
                    json.dumps(receipt.get("blockers", []), ensure_ascii=False),
                    json.dumps(receipt.get("sampled_chunks", []), ensure_ascii=False),
                    json.dumps(receipt, ensure_ascii=False),
                ),
            )
        return self.get(receipt["receipt_id"]) or {}

    def get(self, receipt_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM worker_result_validations WHERE receipt_id = ?", (receipt_id,)).fetchone()
        return self._api(dict(row)) if row else None

    def list(self, node_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if node_id:
                rows = conn.execute("SELECT * FROM worker_result_validations WHERE node_id = ? ORDER BY created_at DESC LIMIT ?", (node_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM worker_result_validations ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._api(dict(row)) for row in rows]

    @staticmethod
    def _api(row: dict[str, Any]) -> dict[str, Any]:
        receipt = json.loads(row.pop("receipt_json"))
        receipt["created_at"] = row["created_at"]
        return receipt


def validate_worker_result(
    worker_result: dict[str, Any],
    artifact_manifest: dict[str, Any] | None = None,
    sample_size: int = 2,
    store: WorkerResultValidationStore | None = None,
    reputation: ReputationOps | None = None,
    apply_reputation: bool = True,
) -> dict[str, Any]:
    blockers: list[str] = []
    binding = worker_result.get("artifact_binding") if isinstance(worker_result.get("artifact_binding"), dict) else {}
    node_id = str(worker_result.get("node_id") or "")
    runtime_id = str(worker_result.get("runtime_id") or "")
    model_manifest_hash = str(worker_result.get("model_manifest_hash") or "")
    artifact_hash = str(binding.get("artifact_hash") or "")

    if not str(worker_result.get("answer") or "").strip():
        blockers.append("empty_answer")
    if not node_id:
        blockers.append("missing_node_id")
    if not runtime_id:
        blockers.append("missing_runtime_id")
    if not model_manifest_hash.startswith("sha256:"):
        blockers.append("missing_model_manifest_hash")
    if not binding:
        blockers.append("missing_artifact_binding")
    elif binding.get("runtime_manifest_hash") != model_manifest_hash:
        blockers.append("runtime_manifest_hash_mismatch")
    if not artifact_hash.startswith("sha256:"):
        blockers.append("missing_artifact_hash")

    sampled_chunks = sample_chunk_provenance(artifact_manifest or {}, sample_size)
    if artifact_manifest:
        manifest_artifact_hash = str(artifact_manifest.get("artifact_hash") or "")
        if artifact_hash and manifest_artifact_hash and artifact_hash != manifest_artifact_hash:
            blockers.append("artifact_hash_mismatch")
        if not sampled_chunks:
            blockers.append("artifact_manifest_no_sampled_chunks")
        for chunk in sampled_chunks:
            if not chunk["ok"]:
                blockers.append("chunk_provenance_failed:" + str(chunk["index"]))

    blockers = sorted(set(blockers))
    score = max(0.0, round(1.0 - 0.25 * len(blockers), 3))
    passed = not blockers
    result_hash = stable_hash(worker_result)
    receipt = {
        "schema_version": WORKER_RESULT_VALIDATION_SCHEMA,
        "receipt_id": "wrv_" + uuid4().hex[:12],
        "result_hash": result_hash,
        "node_id": node_id,
        "runtime_id": runtime_id,
        "model_manifest_hash": model_manifest_hash,
        "artifact_hash": artifact_hash,
        "artifact_binding_id": binding.get("binding_id"),
        "passed": passed,
        "score": score,
        "blockers": blockers,
        "sampled_chunks": sampled_chunks,
    }
    receipt["receipt_hash"] = stable_hash(receipt)

    if store is not None:
        receipt = store.add(receipt)
    if apply_reputation and reputation is not None and node_id:
        delta = 1.0 if passed else -3.0
        receipt["reputation_event"] = reputation.add_event(
            node_id=node_id,
            event_type="worker_result_validation",
            delta=delta,
            reason="worker result validation passed" if passed else "worker result validation failed",
            metadata={"receipt_id": receipt["receipt_id"], "blockers": blockers, "score": score},
        )
    return receipt


def sample_chunk_provenance(artifact_manifest: dict[str, Any], sample_size: int = 2) -> list[dict[str, Any]]:
    chunks = artifact_manifest.get("chunks") if isinstance(artifact_manifest.get("chunks"), list) else []
    if not chunks or sample_size <= 0:
        return []
    count = min(sample_size, len(chunks))
    seed = stable_hash({"artifact_hash": artifact_manifest.get("artifact_hash"), "chunk_count": len(chunks)})
    start = int(seed.removeprefix("sha256:")[:8], 16) % len(chunks)
    sampled: list[dict[str, Any]] = []
    for offset in range(count):
        chunk = chunks[(start + offset) % len(chunks)]
        chunk_hash = str(chunk.get("sha256") or chunk.get("chunk_hash") or chunk.get("hash") or "")
        sources = chunk.get("sources") if isinstance(chunk.get("sources"), list) else []
        index = chunk.get("index", (start + offset) % len(chunks))
        ok = chunk_hash.startswith("sha256:") and bool(sources)
        sampled.append({"index": index, "ok": ok, "chunk_hash": chunk_hash, "sources": sources})
    return sampled


def stable_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()
