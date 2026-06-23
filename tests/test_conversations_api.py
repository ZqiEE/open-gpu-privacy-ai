from fastapi.testclient import TestClient

from api.main import app


def test_native_chat_creates_conversation_and_messages() -> None:
    client = TestClient(app)
    response = client.post(
        "/ailovanta/v1/chat",
        json={"prompt": "hello", "user_id": "pytest", "title": "Pytest chat"},
    )
    assert response.status_code == 200
    body = response.json()
    conversation_id = body["conversation_id"]
    assert conversation_id
    assert body["answer"]

    history = client.get(f"/ailovanta/v1/conversations/{conversation_id}/messages")
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[-1]["role"] == "assistant"


def test_conversation_list_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/ailovanta/v1/conversations", params={"user_id": "pytest"})
    assert response.status_code == 200
    assert "conversations" in response.json()
