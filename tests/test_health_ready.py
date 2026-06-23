from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["service"] == "ailovanta-api"


def test_ready_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["scheduler_store"] == "sqlite"
