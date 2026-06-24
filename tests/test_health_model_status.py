from fastapi.testclient import TestClient

from api.main import app


def test_health_includes_local_model_status() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["local_model"]["adapter"] == "ollama"
    assert body["local_model"]["mode"] == "bootstrap_local_runtime"
    assert body["local_model"]["owned_model_ready"] is False
    assert "model" in body["local_model"]
    assert "base_url" in body["local_model"]
    assert "target_backend" in body["local_model"]
    assert "fallback" in body["local_model"]
