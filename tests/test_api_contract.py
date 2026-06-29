from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app, runtime_registry, store
from api.node_trust import NodeTrustStore
from api.storage import SchedulerStore


def test_root_contract() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ailovanta"
    assert body["app"] == "/app"
    assert body["dashboard"] == "/dashboard"
    assert "scheduler" in body
    assert "runtime" in body


def test_public_pages_are_served() -> None:
    client = TestClient(app)
    app_response = client.get("/app")
    assert app_response.status_code == 200
    assert "Ailovanta" in app_response.text

    dashboard_response = client.get("/dashboard")
    assert dashboard_response.status_code == 200
    assert "Ailovanta Dashboard" in dashboard_response.text


def test_register_node_and_job_flow() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            node = client.post(
                "/nodes/register",
                json={
                    "device_name": "pytest-node",
                    "cpu_threads": 4,
                    "memory_gb": 8,
                    "has_gpu": False,
                    "gpu_name": None,
                    "contribution_percent": 30,
                },
            )
            assert node.status_code == 200
            node_id = node.json()["node_id"]

            job = client.get("/jobs/next", params={"node_id": node_id})
            assert job.status_code == 200
            payload = job.json()["job"]
            assert payload is not None

            result = client.post(
                "/jobs/result",
                json={
                    "node_id": node_id,
                    "job_id": payload["id"],
                    "status": "ok",
                    "output_summary": "simulated pytest result",
                },
            )
            assert result.status_code == 200
            body = result.json()
            assert body["ok"] is True
            assert "verification" in body

            status = client.get("/network/status")
            assert status.status_code == 200
            assert "nodes" in status.json()

            verification = client.get("/verification/status")
            assert verification.status_code == 200
            assert "pass_rate" in verification.json()
        finally:
            store.path = original_path


def test_training_job_and_model_version() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        local_store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        original_path = store.path
        store.path = local_store.path
        try:
            client = TestClient(app)
            job = client.post(
                "/training/jobs",
                json={
                    "kind": "rag_import",
                    "name": "pytest-rag",
                    "dataset_uri": "file://pytest/docs",
                    "base_model": "qwen2.5:3b",
                },
            )
            assert job.status_code == 200
            job_id = job.json()["job"]["id"]

            training_jobs = client.get("/training/jobs")
            assert training_jobs.status_code == 200
            assert any(item["id"] == job_id for item in training_jobs.json()["jobs"])

            exported = client.post(f"/training/jobs/{job_id}/export")
            assert exported.status_code == 200
            assert exported.json()["export"]["payload"]["schema_version"] == "ailovanta.training_job.v1"

            model = client.post(
                "/models/versions",
                json={
                    "name": "pytest-model",
                    "base_model": "qwen2.5:3b",
                    "source_job_id": job_id,
                },
            )
            assert model.status_code == 200
            assert model.json()["model"]["source_job_id"] == job_id
        finally:
            store.path = original_path


def test_runtime_router_prefers_warm_verified_runtime(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    trust = NodeTrustStore()
    trust.register("node-cold", "secret-cold", trust_score=0.95)
    trust.register("node-warm", "secret-warm", trust_score=0.9)
    runtime_registry.clear()
    client = TestClient(app)

    model = client.post(
        "/runtime/models/register",
        json={
            "model_id": "ailovanta-7b",
            "version": "1.0.0",
            "manifest_hash": "sha256:model7b",
            "privacy_level": "public",
            "min_gpu_memory_gb": 8,
            "allowed_pools": ["small_gpu_pool", "large_gpu_pool", "enterprise_pool"],
            "quantization": "int4",
            "context_length": 8192,
        },
    )
    assert model.status_code == 200

    cold = client.post(
        "/runtime/nodes/register",
        json={
            "runtime_id": "rt-cold-fast",
            "node_id": "node-cold",
            "pool": "large_gpu_pool",
            "region": "us-east",
            "gpu_memory_gb": 80,
            "available_gpu_memory_gb": 60,
            "trust_score": 0.95,
            "current_load": 0.1,
            "price_per_1k_tokens": 0.02,
            "latency_ms": 150,
            "supported_engines": ["vllm"],
            "cached_models": [],
        },
    )
    assert cold.status_code == 200

    warm = client.post(
        "/runtime/nodes/register",
        json={
            "runtime_id": "rt-warm-good",
            "node_id": "node-warm",
            "pool": "small_gpu_pool",
            "region": "us-east",
            "gpu_memory_gb": 24,
            "available_gpu_memory_gb": 16,
            "trust_score": 0.9,
            "current_load": 0.2,
            "price_per_1k_tokens": 0.03,
            "latency_ms": 260,
            "supported_engines": ["vllm"],
            "cached_models": ["ailovanta-7b:1.0.0"],
        },
    )
    assert warm.status_code == 200

    routed = client.post(
        "/runtime/route",
        json={
            "request_id": "req-1",
            "model_id": "ailovanta-7b",
            "version": "1.0.0",
            "task_type": "chat_completion",
            "privacy_level": "public",
            "latency_target_ms": 1000,
            "max_price_per_1k_tokens": 0.05,
            "region_hint": "us-east",
            "verification_required": True,
        },
    )
    assert routed.status_code == 200
    body = routed.json()
    assert body["assigned"] is True
    assignment = body["assignment"]
    assert assignment["runtime_id"] == "rt-warm-good"
    assert assignment["cache_state"] == "warm"
    assert assignment["model_manifest_hash"] == "sha256:model7b"


def test_private_runtime_routes_only_to_trusted_pool(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    trust = NodeTrustStore()
    trust.register("node-public-large", "secret-public", trust_score=0.99)
    trust.register("node-trusted", "secret-trusted", trust_score=0.92)
    runtime_registry.clear()
    client = TestClient(app)

    client.post(
        "/runtime/models/register",
        json={
            "model_id": "private-core",
            "version": "1.0.0",
            "manifest_hash": "sha256:private",
            "privacy_level": "private",
            "min_gpu_memory_gb": 16,
            "allowed_pools": ["large_gpu_pool", "trusted_runtime_pool", "enterprise_pool"],
        },
    )
    client.post(
        "/runtime/nodes/register",
        json={
            "runtime_id": "rt-public-large",
            "node_id": "node-public-large",
            "pool": "large_gpu_pool",
            "region": "eu",
            "available_gpu_memory_gb": 80,
            "trust_score": 0.99,
            "current_load": 0.0,
            "price_per_1k_tokens": 0.02,
            "latency_ms": 100,
            "cached_models": ["private-core:1.0.0"],
        },
    )
    client.post(
        "/runtime/nodes/register",
        json={
            "runtime_id": "rt-trusted",
            "node_id": "node-trusted",
            "pool": "trusted_runtime_pool",
            "region": "eu",
            "available_gpu_memory_gb": 32,
            "trust_score": 0.92,
            "current_load": 0.2,
            "price_per_1k_tokens": 0.05,
            "latency_ms": 300,
            "cached_models": ["private-core:1.0.0"],
        },
    )

    routed = client.post(
        "/runtime/route",
        json={
            "request_id": "req-private",
            "model_id": "private-core",
            "version": "1.0.0",
            "privacy_level": "private",
            "latency_target_ms": 1000,
            "max_price_per_1k_tokens": 0.1,
            "region_hint": "eu",
        },
    )
    assert routed.status_code == 200
    assignment = routed.json()["assignment"]
    assert assignment["runtime_id"] == "rt-trusted"
    assert assignment["pool"] == "trusted_runtime_pool"
