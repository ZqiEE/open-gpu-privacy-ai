from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from api.node_trust import NodeTrustStore
from api.prod_config import load_config
from api.runtime_router import ModelManifest, RuntimeNodeProfile, RuntimeRegistry, RuntimeRequest
from api.sqlite_utils import connect_sqlite


class RuntimeStore:
    def __init__(self, path: str | Path = "runtime_data/runtime.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runtime_models (
                    model_key TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    manifest_hash TEXT NOT NULL,
                    privacy_level TEXT NOT NULL,
                    min_gpu_memory_gb REAL NOT NULL,
                    allowed_pools_json TEXT NOT NULL,
                    quantization TEXT NOT NULL,
                    context_length INTEGER NOT NULL,
                    adapter_compatible INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runtime_nodes (
                    runtime_id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    pool TEXT NOT NULL,
                    region TEXT NOT NULL,
                    status TEXT NOT NULL,
                    gpu_memory_gb REAL NOT NULL,
                    available_gpu_memory_gb REAL NOT NULL,
                    trust_score REAL NOT NULL,
                    current_load REAL NOT NULL,
                    price_per_1k_tokens REAL NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    supported_engines_json TEXT NOT NULL,
                    cached_models_json TEXT NOT NULL,
                    cached_adapters_json TEXT NOT NULL,
                    last_heartbeat REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runtime_assignments (
                    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    model_key TEXT NOT NULL,
                    runtime_id TEXT,
                    node_id TEXT,
                    pool TEXT,
                    region TEXT,
                    cache_state TEXT,
                    model_manifest_hash TEXT,
                    estimated_latency_ms INTEGER,
                    price_per_1k_tokens REAL,
                    verification_required INTEGER,
                    score REAL,
                    assigned INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def register_model(self, manifest: ModelManifest) -> dict:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runtime_models VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.key,
                    manifest.model_id,
                    manifest.version,
                    manifest.manifest_hash,
                    manifest.privacy_level,
                    manifest.min_gpu_memory_gb,
                    json.dumps(manifest.allowed_pools),
                    manifest.quantization,
                    manifest.context_length,
                    1 if manifest.adapter_compatible else 0,
                    manifest.status,
                    manifest.created_at,
                ),
            )
        return self.get_model(manifest.key) or {}

    def get_model(self, model_key: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
        return self._api_model(dict(row)) if row else None

    def list_models(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM runtime_models ORDER BY model_key ASC").fetchall()
        return [self._api_model(dict(row)) for row in rows]

    def register_runtime(self, profile: RuntimeNodeProfile) -> dict:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runtime_nodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.runtime_id,
                    profile.node_id,
                    profile.pool,
                    profile.region,
                    profile.status,
                    profile.gpu_memory_gb,
                    profile.available_gpu_memory_gb,
                    profile.trust_score,
                    profile.current_load,
                    profile.price_per_1k_tokens,
                    profile.latency_ms,
                    json.dumps(profile.supported_engines),
                    json.dumps(profile.cached_models),
                    json.dumps(profile.cached_adapters),
                    profile.last_heartbeat,
                ),
            )
        return self.get_runtime(profile.runtime_id) or {}

    def get_runtime(self, runtime_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM runtime_nodes WHERE runtime_id = ?", (runtime_id,)).fetchone()
        return self._api_runtime(dict(row)) if row else None

    def list_runtimes(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM runtime_nodes ORDER BY runtime_id ASC").fetchall()
        return [self._api_runtime(dict(row)) for row in rows]

    @staticmethod
    def runtime_trust_check(runtime: dict[str, Any], trust: NodeTrustStore | None = None) -> dict[str, Any]:
        cfg = load_config()
        node_id = str(runtime.get("node_id") or "")
        if not node_id:
            return {"ok": False, "reason": "missing_node_id"}
        item = (trust or NodeTrustStore()).get(node_id)
        if not item:
            return {"ok": False, "reason": "unknown_node", "node_id": node_id}
        if item.get("status") != "active":
            return {"ok": False, "reason": "node_not_active", "node_id": node_id, "status": item.get("status")}
        trust_score = float(item.get("trust_score") or 0.0)
        if trust_score < cfg.min_avg_trust_score:
            return {"ok": False, "reason": "node_trust_too_low", "node_id": node_id, "trust_score": trust_score, "min_trust_score": cfg.min_avg_trust_score}
        return {"ok": True, "node_id": node_id, "trust_score": trust_score, "status": item.get("status")}

    def route(self, request: RuntimeRequest) -> dict:
        registry = RuntimeRegistry()
        for model in self.list_models():
            registry.register_model(self._model_from_api(model))
        rejected: list[dict[str, Any]] = []
        for runtime in self.list_runtimes():
            check = self.runtime_trust_check(runtime)
            if request.verification_required and not check.get("ok"):
                rejected.append({"runtime_id": runtime.get("runtime_id"), "node_id": runtime.get("node_id"), "reason": check.get("reason"), "check": check})
                continue
            if check.get("ok"):
                runtime = {**runtime, "trust_score": check.get("trust_score", runtime.get("trust_score", 0.0))}
            registry.register_runtime(self._runtime_from_api(runtime))
        routed = registry.route(request)
        if rejected:
            routed["rejected_runtimes"] = rejected[:50]
        self.record_assignment(request, routed)
        return routed

    def record_assignment(self, request: RuntimeRequest, routed: dict) -> None:
        assignment = routed.get("assignment") or {}
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_assignments (
                    request_id, model_key, runtime_id, node_id, pool, region,
                    cache_state, model_manifest_hash, estimated_latency_ms,
                    price_per_1k_tokens, verification_required, score, assigned, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    request.model_key,
                    assignment.get("runtime_id"),
                    assignment.get("node_id"),
                    assignment.get("pool"),
                    assignment.get("region"),
                    assignment.get("cache_state"),
                    assignment.get("model_manifest_hash") or routed.get("model_manifest_hash"),
                    assignment.get("estimated_latency_ms"),
                    assignment.get("price_per_1k_tokens"),
                    1 if request.verification_required else 0,
                    assignment.get("score"),
                    1 if routed.get("assigned") else 0,
                    routed.get("reason") or assignment.get("reason") or "unknown",
                ),
            )

    def list_assignments(self, limit: int = 50) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM runtime_assignments ORDER BY assignment_id DESC LIMIT ?", (limit,)).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["assigned"] = bool(item["assigned"])
            item["verification_required"] = bool(item["verification_required"])
            items.append(item)
        return items

    def status(self) -> dict:
        with self.connect() as conn:
            models = conn.execute("SELECT COUNT(*) FROM runtime_models").fetchone()[0]
            runtimes = conn.execute("SELECT COUNT(*) FROM runtime_nodes").fetchone()[0]
            online = conn.execute("SELECT COUNT(*) FROM runtime_nodes WHERE status = 'online'").fetchone()[0]
            route_attempts = conn.execute("SELECT COUNT(*) FROM runtime_assignments").fetchone()[0]
            successful = conn.execute("SELECT COUNT(*) FROM runtime_assignments WHERE assigned = 1").fetchone()[0]
            rows = conn.execute("SELECT cached_models_json FROM runtime_nodes").fetchall()
        warm_links = sum(len(json.loads(row[0])) for row in rows)
        return {"models": models, "runtimes": runtimes, "online_runtimes": online, "warm_model_links": warm_links, "route_attempts": route_attempts, "successful_routes": successful, "store": "sqlite", "path": str(self.path)}

    def clear(self) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM runtime_assignments")
            conn.execute("DELETE FROM runtime_nodes")
            conn.execute("DELETE FROM runtime_models")

    @staticmethod
    def _api_model(row: dict[str, Any]) -> dict:
        return {"model_id": row["model_id"], "version": row["version"], "model_key": row["model_key"], "manifest_hash": row["manifest_hash"], "privacy_level": row["privacy_level"], "min_gpu_memory_gb": row["min_gpu_memory_gb"], "allowed_pools": json.loads(row["allowed_pools_json"]), "quantization": row["quantization"], "context_length": row["context_length"], "adapter_compatible": bool(row["adapter_compatible"]), "status": row["status"], "created_at": row["created_at"]}

    @staticmethod
    def _api_runtime(row: dict[str, Any]) -> dict:
        return {"runtime_id": row["runtime_id"], "node_id": row["node_id"], "pool": row["pool"], "region": row["region"], "status": row["status"], "gpu_memory_gb": row["gpu_memory_gb"], "available_gpu_memory_gb": row["available_gpu_memory_gb"], "trust_score": row["trust_score"], "current_load": row["current_load"], "price_per_1k_tokens": row["price_per_1k_tokens"], "latency_ms": row["latency_ms"], "supported_engines": json.loads(row["supported_engines_json"]), "cached_models": json.loads(row["cached_models_json"]), "cached_adapters": json.loads(row["cached_adapters_json"]), "last_heartbeat": row["last_heartbeat"]}

    @staticmethod
    def _model_from_api(body: dict[str, Any]) -> ModelManifest:
        return ModelManifest(model_id=body["model_id"], version=body["version"], manifest_hash=body["manifest_hash"], privacy_level=body["privacy_level"], min_gpu_memory_gb=body["min_gpu_memory_gb"], allowed_pools=body["allowed_pools"], quantization=body["quantization"], context_length=body["context_length"], adapter_compatible=body["adapter_compatible"], status=body["status"], created_at=body["created_at"])

    @staticmethod
    def _runtime_from_api(body: dict[str, Any]) -> RuntimeNodeProfile:
        return RuntimeNodeProfile(runtime_id=body["runtime_id"], node_id=body["node_id"], pool=body["pool"], region=body["region"], status=body["status"], gpu_memory_gb=body["gpu_memory_gb"], available_gpu_memory_gb=body["available_gpu_memory_gb"], trust_score=body["trust_score"], current_load=body["current_load"], price_per_1k_tokens=body["price_per_1k_tokens"], latency_ms=body["latency_ms"], supported_engines=body["supported_engines"], cached_models=body["cached_models"], cached_adapters=body["cached_adapters"], last_heartbeat=body["last_heartbeat"])
