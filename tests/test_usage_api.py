from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_usage_api_contract() -> None:
    client = TestClient(app)
    event = client.post(
        "/usage/events",
        json={"user_id": "pytest-usage", "event_type": "chat", "quantity": 1, "source": "pytest"},
    )
    assert event.status_code == 200
    assert event.json()["ok"] is True

    summary = client.get("/usage/summary", params={"user_id": "pytest-usage"})
    assert summary.status_code == 200
    assert summary.json()["by_type"]["chat"] >= 1

    events = client.get("/usage/events", params={"user_id": "pytest-usage"})
    assert events.status_code == 200
    assert "events" in events.json()
