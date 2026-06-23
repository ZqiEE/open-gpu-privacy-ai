from fastapi.testclient import TestClient

from api.main import app


def test_v1_chat_completion_returns_choice() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={"model": "ailovanta-local", "messages": [{"role": "user", "content": "hello"}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"]
