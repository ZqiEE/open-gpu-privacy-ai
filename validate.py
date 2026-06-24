from pathlib import Path

root = Path(__file__).resolve().parent

required_files = [
    "README.md",
    "VERSION",
    "index.html",
    "api/main.py",
    "api/auth_store.py",
    "api/github_auth.py",
    "api/conversation_context.py",
    "api/conversation_store.py",
    "api/ailovanta_native.py",
    "api/openai_compat.py",
    "api/reputation.py",
    "api/runtime_router.py",
    "api/runtime_store.py",
    "api/usage_store.py",
    "docs/AUTH_MODEL.md",
    "docs/GITHUB_AUTH_SETUP.md",
    "docs/NEXT_STAGE_PRD.md",
    "docs/NEXT_STAGE_CODEX_TASKS.md",
    "docs/NATIVE_RUN_API.md",
    "docs/V1_CHAT_API.md",
    "tests/test_conversation_context.py",
    "tests/test_frontend_markers.py",
    "tests/test_guest_chat_flow.py",
    "tests/test_health_model_status.py",
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
assert version in {"1.9.0-github-auth", "1.10.0-guest-first", "1.11.0"}, f"unexpected version: {version}"

checks = {
    "index.html": ["guest mode", "No login required", "No payment required", "/ailovanta/v1/chat", "guest_id", "conversationList", "Model adapter", "Fallback: enabled"],
    "api/health.py": ["local_model", "ollama", "base_url", "fallback"],
    "api/main.py": [
        "build_chat_context",
        "context_messages_used",
        "/ailovanta/v1/chat",
        "/ailovanta/v1/run",
        "/reputation/leaderboard",
        "/reputation/summary",
        "/usage/events",
    ],
    "api/conversation_context.py": ["build_chat_context", "context_to_text", "max_messages"],
    "api/conversation_store.py": ["ConversationStore", "conversations", "conversation_messages", "add_message"],
    "api/ollama_adapter.py": ["chat_messages", "conversation history", "Use the provided conversation history"],
    "api/reputation.py": ["ReputationService", "leaderboard", "summary", "reputation_score"],
    "api/usage_store.py": ["UsageStore", "usage_events", "record", "list_events"],
    "docs/AUTH_MODEL.md": ["Guest mode first", "No required login", "First prove value"],
    "docs/PAYMENT_MODEL.md": ["No payment required", "No paywall", "First prove value"],
    "docs/NEXT_STAGE_PRD.md": ["Guest Chat Core", "多轮上下文注入", "无登录墙", "无付费墙"],
    "tests/test_conversation_context.py": ["build_chat_context", "context_to_text"],
    "tests/test_frontend_markers.py": ["conversationList", "No login required", "context_messages_used"],
    "tests/test_guest_chat_flow.py": ["context_messages_used", "/ailovanta/v1/conversations", "/reputation/leaderboard"],
    "tests/test_health_model_status.py": ["local_model", "ollama", "base_url"],
    "tests/test_reputation.py": ["/reputation/leaderboard", "/reputation/summary"],
    "tests/test_usage_api.py": ["/usage/events", "/usage/summary"],
}

for rel, markers in checks.items():
    text = (root / rel).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"missing marker {marker} in {rel}"

print("Ailovanta validation passed.")
