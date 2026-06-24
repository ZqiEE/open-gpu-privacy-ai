from pathlib import Path

root = Path(__file__).resolve().parent

required_files = [
    "README.md",
    "VERSION",
    "index.html",
    "api/main.py",
    "api/auth_store.py",
    "api/github_auth.py",
    "api/conversation_store.py",
    "api/ailovanta_native.py",
    "api/openai_compat.py",
    "api/reputation.py",
    "api/runtime_router.py",
    "api/runtime_store.py",
    "api/usage_store.py",
    "docs/AUTH_MODEL.md",
    "docs/GITHUB_AUTH_SETUP.md",
    "docs/NATIVE_RUN_API.md",
    "docs/V1_CHAT_API.md",
    "tests/test_github_auth_api.py",
    "tests/test_conversations_api.py",
    "tests/test_native_run_api.py",
    "tests/test_chat_api.py",
    "tests/test_reputation.py",
    "tests/test_usage_api.py",
    ".github/workflows/validate.yml",
]

for rel in required_files:
    path = root / rel
    assert path.exists(), f"missing file: {rel}"

version = (root / "VERSION").read_text(encoding="utf-8").strip()
assert version in {"1.9.0-github-auth", "1.10.0-guest-first"}, f"unexpected version: {version}"

checks = {
    "index.html": ["guest mode", "No login required", "/ailovanta/v1/chat", "guest_id"],
    "api/main.py": [
        "AuthStore",
        "/auth/github/login",
        "/auth/me",
        "/ailovanta/v1/chat",
        "/ailovanta/v1/run",
        "/reputation/leaderboard",
        "/reputation/summary",
        "/usage/events",
    ],
    "api/auth_store.py": ["AuthStore", "auth_states", "users", "sessions", "create_session"],
    "api/github_auth.py": ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "build_github_login_url", "fetch_github_profile"],
    "api/conversation_store.py": ["ConversationStore", "conversations", "conversation_messages", "add_message"],
    "api/reputation.py": ["ReputationService", "leaderboard", "summary", "reputation_score"],
    "api/usage_store.py": ["UsageStore", "usage_events", "record", "list_events"],
    "docs/AUTH_MODEL.md": ["Guest mode first", "No required login", "First prove value"],
    "docs/GITHUB_AUTH_SETUP.md": ["GitHub Auth Setup", "GITHUB_CLIENT_ID", "/auth/github/callback"],
    "tests/test_github_auth_api.py": ["/auth/github/login", "AuthStore", "revoke_session"],
    "tests/test_reputation.py": ["/reputation/leaderboard", "/reputation/summary"],
    "tests/test_usage_api.py": ["/usage/events", "/usage/summary"],
}

for rel, markers in checks.items():
    text = (root / rel).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"missing marker {marker} in {rel}"

print("Ailovanta validation passed.")
