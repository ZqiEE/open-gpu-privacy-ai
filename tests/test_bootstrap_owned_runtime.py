from fastapi.testclient import TestClient

import api.main as main_module
from api.artifact_binding import ArtifactBindingStore
from api.main import app
from api.runtime_forwarder import RuntimeEndpointStore
from scripts.bootstrap_owned_runtime import bootstrap_owned_runtime


def test_bootstrap_owned_runtime_enables_owned_chat(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "node_trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "artifact_bindings.sqlite3"))
    monkeypatch.setenv("AILOVANTA_ROUTE_BOOK_PATH", str(tmp_path / "route_book.sqlite3"))
    monkeypatch.setenv("AILOVANTA_RUNTIME_ENDPOINTS_PATH", str(tmp_path / "runtime_endpoints.json"))
    monkeypatch.setenv("AILOVANTA_WORKER_VALIDATION_PATH", str(tmp_path / "worker_validations.sqlite3"))
    monkeypatch.setattr(main_module.runtime_registry, "path", tmp_path / "runtime.sqlite3")
    main_module.runtime_registry._init_db()
    main_module.runtime_registry.clear()

    result = bootstrap_owned_runtime(tmp_path)
    client = TestClient(app)
    response = client.post("/ailovanta/v1/chat", json={"prompt": "hello"})
    body = response.json()

    assert result["ok"] is True
    assert RuntimeEndpointStore(tmp_path / "runtime_endpoints.json").get("rt-owned-1")["url"] == "inprocess://ailovanta-worker"
    assert response.status_code == 200
    assert body["owned_model_ready"] is True
    assert body["source"] == "ailovanta-worker"
    assert "不是已训练完成" in body["answer"]
    assert "Loaded the local checkpoint metadata" not in body["answer"]


def test_bootstrap_owned_runtime_does_not_overwrite_training_artifact(tmp_path) -> None:
    store = ArtifactBindingStore(tmp_path / "artifact_bindings.sqlite3")
    model_path = tmp_path / "ngram_model.json"
    model_path.write_text('{"schema":"ailovanta.lightweight_ngram.v1","rows":1}', encoding="utf-8")
    trained = store.register_binding(
        {
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "model_key": "ailovanta-owned:candidate",
            "manifest_hash": "sha256:local-owned-candidate",
            "status": "active",
        },
        {
            "artifact_id": "local_training_test",
            "artifact_hash": "sha256:trained",
            "checkpoint_uri": "file://" + str(model_path),
        },
        backend_kind="lightweight-ngram",
        backend_ref="file://" + str(model_path),
        status="active",
    )

    result = bootstrap_owned_runtime(tmp_path)
    latest = ArtifactBindingStore(tmp_path / "artifact_bindings.sqlite3").latest_for_model("ailovanta-owned:candidate", active_only=True)

    assert result["binding"]["binding_id"] == trained["binding_id"]
    assert latest["backend_kind"] == "lightweight-ngram"
