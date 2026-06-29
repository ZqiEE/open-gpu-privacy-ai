from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, runtime_registry, store
from api.node_trust import NodeTrustStore
from api.runtime_store import RuntimeStore
from api.storage import SchedulerStore
from api.worker_result_validator import WorkerResultValidationStore


def test_owned_runtime_dashboard_surfaces_route_validation_and_reputation(monkeypatch, tmp_path: Path) -> None:
    original_runtime = runtime_registry
    original_store_path = store.path
    import api.main as main_module

    main_module.runtime_registry = RuntimeStore(tmp_path / "runtime.sqlite3")
    store.path = SchedulerStore(tmp_path / "scheduler.sqlite3").path
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_WORKER_VALIDATION_PATH", str(tmp_path / "worker_validations.sqlite3"))
    monkeypatch.setenv("AILOVANTA_REPUTATION_PATH", str(tmp_path / "scheduler.sqlite3"))

    try:
        NodeTrustStore().register("node-owned-dashboard", "secret", trust_score=0.9)
        client = TestClient(app)
        client.post(
            "/nodes/register",
            json={
                "node_id": "node-owned-dashboard",
                "device_name": "owned-dashboard",
                "cpu_threads": 8,
                "memory_gb": 16,
                "has_gpu": True,
                "gpu_name": "test",
                "contribution_percent": 30,
            },
        )
        client.post(
            "/runtime/models/register",
            json={
                "model_id": "ailovanta-owned",
                "version": "candidate",
                "manifest_hash": "sha256:runtime",
                "privacy_level": "protected",
                "min_gpu_memory_gb": 0,
                "allowed_pools": ["trusted_runtime_pool"],
            },
        )
        client.post(
            "/runtime/nodes/register",
            json={
                "runtime_id": "rt-owned-dashboard",
                "node_id": "node-owned-dashboard",
                "pool": "trusted_runtime_pool",
                "region": "global",
                "status": "online",
                "gpu_memory_gb": 24,
                "available_gpu_memory_gb": 20,
                "trust_score": 0.9,
                "current_load": 0.1,
                "price_per_1k_tokens": 0.01,
                "latency_ms": 100,
                "cached_models": ["ailovanta-owned:candidate"],
            },
        )
        route = client.post(
            "/runtime/route",
            json={
                "request_id": "dashboard-route",
                "model_id": "ailovanta-owned",
                "version": "candidate",
                "task_type": "chat_completion",
                "privacy_level": "protected",
                "verification_required": True,
            },
        )
        assert route.status_code == 200
        WorkerResultValidationStore(tmp_path / "worker_validations.sqlite3").add(
            {
                "schema_version": "ailovanta.worker_result_validation.v1",
                "receipt_id": "wrv_dashboard",
                "result_hash": "sha256:result",
                "node_id": "node-owned-dashboard",
                "runtime_id": "rt-owned-dashboard",
                "model_manifest_hash": "sha256:runtime",
                "artifact_hash": "sha256:artifact",
                "artifact_binding_id": "binding-dashboard",
                "passed": True,
                "score": 1.0,
                "blockers": [],
                "sampled_chunks": [{"index": 0, "ok": True, "chunk_hash": "sha256:chunk", "sources": ["node://node-owned-dashboard/checkpoint.bin"]}],
                "receipt_hash": "sha256:receipt",
            }
        )
        client.post(
            "/worker-results/validate",
            json={
                "worker_result": {
                    "answer": "ok",
                    "node_id": "node-owned-dashboard",
                    "runtime_id": "rt-owned-dashboard",
                    "model_manifest_hash": "sha256:runtime",
                    "artifact_binding": {
                        "binding_id": "binding-dashboard-2",
                        "runtime_manifest_hash": "sha256:runtime",
                        "artifact_hash": "sha256:artifact",
                    },
                },
                "apply_reputation": True,
            },
        )

        response = client.get("/dashboard/owned-runtime")
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["runtime"]["online_runtimes"] == 1
        assert body["route"]["recent_successful_assignment"]["runtime_id"] == "rt-owned-dashboard"
        assert body["worker_validation"]["recent_receipt_count"] >= 1
        assert body["worker_validation"]["pass_rate"] == 1.0
        assert body["reputation"]["event_count"] >= 1
    finally:
        main_module.runtime_registry = original_runtime
        store.path = original_store_path
