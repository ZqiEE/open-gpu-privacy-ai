from pathlib import Path

root = Path(__file__).resolve().parent

required_files = [
    "README.md",
    "VERSION",
    "index.html",
    "api/main.py",
    "api/auth_store.py",
    "api/github_auth.py",
    "api/sqlite_utils.py",
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
    "docs/CHATGPT_STYLE_UI.md",
    "docs/NATIVE_RUN_API.md",
    "docs/V1_CHAT_API.md",
    "tests/test_chatgpt_ui_markers.py",
    "tests/test_conversation_context.py",
    "tests/test_frontend_markers.py",
    "tests/test_guest_chat_flow.py",
    "tests/test_health_model_status.py",
    "tests/test_sqlite_utils.py",
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
    "index.html": ["Guest mode first", "No login required", "No payment required", "/ailovanta/v1/chat", "guest_id", "conversationList", "Model adapter", "Fallback: enabled", "Message Ailovanta", "How can I help?", "Enter to send", "Shift+Enter", "markdownLite", "Thinking..."],
    "api/sqlite_utils.py": ["ClosingConnection", "connect_sqlite", "self.close()"],
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
    "api/conversation_store.py": ["connect_sqlite", "ConversationStore", "conversations", "conversation_messages", "add_message"],
    "api/runtime_store.py": ["connect_sqlite", "RuntimeStore", "runtime_models", "runtime_nodes"],
    "api/ollama_adapter.py": ["chat_messages", "conversation history", "Use the provided conversation history"],
    "api/reputation.py": ["ReputationService", "leaderboard", "summary", "reputation_score"],
    "api/usage_store.py": ["connect_sqlite", "UsageStore", "usage_events", "record", "list_events"],
    "docs/AUTH_MODEL.md": ["Guest mode first", "No required login", "First prove value"],
    "docs/PAYMENT_MODEL.md": ["No payment required", "No paywall", "First prove value"],
    "docs/NEXT_STAGE_PRD.md": ["Guest Chat Core", "多轮上下文注入", "无登录墙", "无付费墙"],
    "docs/CHATGPT_STYLE_UI.md": ["ChatGPT-style", "sticky composer", "No Node.js", "true streaming response"],
    "tests/test_chatgpt_ui_markers.py": ["Message Ailovanta", "markdownLite", "Thinking..."],
    "tests/test_conversation_context.py": ["build_chat_context", "context_to_text"],
    "tests/test_frontend_markers.py": ["conversationList", "No login required", "Enter to send", "Thinking..."],
    "tests/test_guest_chat_flow.py": ["context_messages_used", "/ailovanta/v1/conversations", "/reputation/leaderboard"],
    "tests/test_health_model_status.py": ["local_model", "ollama", "base_url"],
    "tests/test_sqlite_utils.py": ["connect_sqlite", "os.remove"],
    "tests/test_reputation.py": ["/reputation/leaderboard", "/reputation/summary"],
    "tests/test_usage_api.py": ["/usage/events", "/usage/summary"],
}

for rel, markers in checks.items():
    text = (root / rel).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"missing marker {marker} in {rel}"

print("Ailovanta validation passed.")
