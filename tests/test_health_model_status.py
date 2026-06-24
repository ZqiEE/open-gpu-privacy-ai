from fastapi.testclient import TestClient

from api.main import app


def test_health_includes_local_model_status() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["local_model"]["adapter"] == "ollama"
    assert "model" in body["local_model"]
    assert "base_url" in body["local_model"]
    assert "fallback" in body["local_model"]
