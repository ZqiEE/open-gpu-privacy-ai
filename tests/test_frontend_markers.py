from pathlib import Path


def test_frontend_contains_guest_chat_controls() -> None:
    html = Path("index.html").read_text(encoding="utf-8")

    for marker in [
        "No login required",
        "No payment required",
        "Guest mode first",
        "conversationList",
        "New chat",
        "Delete chat",
        "Reset guest id",
        "Copy chat",
        "Enter to send",
        "Shift+Enter",
        "Thinking...",
        "copyCurrentChat",
        "/ailovanta/v1/chat",
        "/ailovanta/v1/conversations",
        "context_messages_used",
    ]:
        assert marker in html
