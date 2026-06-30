from fastapi.testclient import TestClient

from api.main import app, runtime_registry
from api.node_trust import NodeTrustStore
from api.worker_transport import WorkerInferenceResult


class FakeWorkerClient:
    def infer(self, request):
        return WorkerInferenceResult(
            answer="owned worker answer",
            source="test-owned-worker",
            worker_url="http://worker.local",
            runtime_id=request.runtime_id,
            node_id=request.node_id,
            raw={
                "answer": "owned worker answer",
                "source": "test-owned-worker",
                "model_id": request.model_id,
                "version": request.version,
                "runtime_id": request.runtime_id,
                "node_id": request.node_id,
                "model_manifest_hash": request.model_manifest_hash,
                "artifact_binding": {
                    "binding_id": "binding-owned-1",
                    "runtime_manifest_hash": request.model_manifest_hash,
                    "artifact_hash": "sha256:artifact",
                    "backend_kind": "checkpoint-artifact",
                },
                "validation_provenance": {
                    "schema_version": "ailovanta.worker_result_provenance.v1",
                    "binding_id": "binding-owned-1",
                    "runtime_manifest_hash": request.model_manifest_hash,
                    "artifact_hash": "sha256:artifact",
                },
            },
        )


def test_native_chat_requires_owned_runtime(monkeypatch, tmp_path) -> None:
    import api.owned_model_runtime as owned_module

    monkeypatch.setenv("AILOVANTA_REQUIRE_OWNED_MODEL", "true")
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_WORKER_VALIDATION_PATH", str(tmp_path / "worker_validations.sqlite3"))
    monkeypatch.setattr(owned_module, "WorkerInferenceClient", lambda: FakeWorkerClient())
    NodeTrustStore().register("node-owned-1", "secret", trust_score=0.9)
    runtime_registry.clear()
    client = TestClient(app)

    client.post(
        "/runtime/models/register",
        json={
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "manifest_hash": "sha256:model",
            "privacy_level": "protected",
            "min_gpu_memory_gb": 0,
            "allowed_pools": ["trusted_runtime_pool"],
        },
    )
    client.post(
        "/runtime/nodes/register",
        json={
            "runtime_id": "rt-owned-1",
            "node_id": "node-owned-1",
            "pool": "trusted_runtime_pool",
            "region": "global",
            "gpu_memory_gb": 24,
            "available_gpu_memory_gb": 20,
            "trust_score": 0.9,
            "current_load": 0.1,
            "price_per_1k_tokens": 0.01,
            "latency_ms": 100,
            "cached_models": ["ailovanta-owned:candidate"],
        },
    )

    response = client.post("/ailovanta/v1/chat", json={"prompt": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["owned_model_ready"] is True
    assert body["answer"] == "owned worker answer"
    assert body["source"] == "test-owned-worker"
    assert body["runtime_route"]["assignment"]["runtime_id"] == "rt-owned-1"
    assert body["worker_validation"]["passed"] is True
    assert body["worker_validation"]["receipt_id"].startswith("wrv_")


def test_native_chat_prefers_owned_runtime_by_default(monkeypatch, tmp_path) -> None:
    import api.owned_model_runtime as owned_module

    monkeypatch.delenv("AILOVANTA_REQUIRE_OWNED_MODEL", raising=False)
    monkeypatch.delenv("AILOVANTA_PREFER_OWNED_MODEL", raising=False)
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_WORKER_VALIDATION_PATH", str(tmp_path / "worker_validations.sqlite3"))
    monkeypatch.setattr(owned_module, "WorkerInferenceClient", lambda: FakeWorkerClient())
    NodeTrustStore().register("node-owned-1", "secret", trust_score=0.9)
    runtime_registry.clear()
    client = TestClient(app)

    client.post(
        "/runtime/models/register",
        json={
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "manifest_hash": "sha256:model",
            "privacy_level": "protected",
            "min_gpu_memory_gb": 0,
            "allowed_pools": ["trusted_runtime_pool"],
        },
    )
    client.post(
        "/runtime/nodes/register",
        json={
            "runtime_id": "rt-owned-1",
            "node_id": "node-owned-1",
            "pool": "trusted_runtime_pool",
            "region": "global",
            "gpu_memory_gb": 24,
            "available_gpu_memory_gb": 20,
            "trust_score": 0.9,
            "current_load": 0.1,
            "price_per_1k_tokens": 0.01,
            "latency_ms": 100,
            "cached_models": ["ailovanta-owned:candidate"],
        },
    )

    response = client.post("/ailovanta/v1/chat", json={"prompt": "hello"})
    body = response.json()

    assert response.status_code == 200
    assert body["owned_model_ready"] is True
    assert body["source"] == "test-owned-worker"
    assert body["answer"] == "owned worker answer"


def test_native_chat_owned_mode_does_not_fallback(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AILOVANTA_REQUIRE_OWNED_MODEL", "true")
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    runtime_registry.clear()
    client = TestClient(app)

    response = client.post("/ailovanta/v1/chat", json={"prompt": "hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["owned_model_ready"] is False
    assert body["source"] == "owned-runtime-unavailable"
    assert "not ready" in body["answer"]


def test_native_chat_can_disable_owned_preference(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_REQUIRE_OWNED_MODEL", raising=False)
    monkeypatch.setenv("AILOVANTA_PREFER_OWNED_MODEL", "false")
    runtime_registry.clear()
    client = TestClient(app)

    response = client.post("/ailovanta/v1/chat", json={"prompt": "hello"})
    body = response.json()

    assert response.status_code == 200
    assert body["owned_model_ready"] is False
    assert body["owned_runtime_error"] is None
