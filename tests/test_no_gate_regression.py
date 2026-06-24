from pathlib import Path


def test_guest_first_docs_do_not_require_login_or_payment() -> None:
    auth = Path("docs/AUTH_MODEL.md").read_text(encoding="utf-8")
    payment = Path("docs/PAYMENT_MODEL.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Guest mode first" in auth
    assert "No required login" in auth
    assert "No required payment" in auth
    assert "No payment required" in payment
    assert "No paywall" in payment
    assert "Guest mode first" in readme


def test_frontend_default_path_is_guest_chat() -> None:
    html = Path("index.html").read_text(encoding="utf-8")

    assert "No login required" in html
    assert "No payment required" in html
    assert "guest_id" in html
    assert "/ailovanta/v1/chat" in html
    assert "conversationList" in html

    forbidden_gate_phrases = [
        "Choose access first",
        "Use paid mode",
        "Access: locked",
        "Login required",
        "Payment required",
    ]
    for phrase in forbidden_gate_phrases:
        assert phrase not in html
