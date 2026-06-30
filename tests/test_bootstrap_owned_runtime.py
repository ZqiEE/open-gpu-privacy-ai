from fastapi.testclient import TestClient

from api.main import app, runtime_registry
from api.runtime_forwarder import RuntimeEndpointStore
from scripts.bootstrap_owned_runtime import bootstrap_owned_runtime


def test_bootstrap_owned_runtime_enables_owned_chat(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "artifact_bindings.sqlite3"))
    monkeypatch.setenv("AILOVANTA_RUNTIME_ENDPOINTS_PATH", str(tmp_path / "runtime_endpoints.json"))
    monkeypatch.setenv("AILOVANTA_WORKER_VALIDATION_PATH", str(tmp_path / "worker_validations.sqlite3"))
    monkeypatch.setattr(runtime_registry, "path", tmp_path / "runtime.sqlite3")
    runtime_registry._init_db()
    runtime_registry.clear()

    result = bootstrap_owned_runtime(tmp_path)
    client = TestClient(app)
    response = client.post("/ailovanta/v1/chat", json={"prompt": "hello"})
    body = response.json()

    assert result["ok"] is True
    assert RuntimeEndpointStore(tmp_path / "runtime_endpoints.json").get("rt-owned-1")["url"] == "inprocess://ailovanta-worker"
    assert response.status_code == 200
    assert body["owned_model_ready"] is True
    assert body["source"] == "ailovanta-worker"
    assert "Loaded the local checkpoint metadata" in body["answer"]
