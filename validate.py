from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parent


class UiContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.classes: set[str] = set()
        self.data_regions: set[str] = set()
        self.data_actions: set[str] = set()
        self.body_attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        self.tags.append((tag, attr))
        if tag == "body":
            self.body_attrs = attr
        if "id" in attr:
            self.ids.add(attr["id"])
        for cls in attr.get("class", "").split():
            self.classes.add(cls)
        if "data-region" in attr:
            self.data_regions.add(attr["data-region"])
        if "data-action" in attr:
            self.data_actions.add(attr["data-action"])


def read(rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    assert condition, message


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
    "docs/UI_VALIDATION_CONTRACT.md",
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
    require((root / rel).exists(), f"missing file: {rel}")

version = read("VERSION").strip()
require(version in {"1.9.0-github-auth", "1.10.0-guest-first", "1.11.0"}, f"unexpected version: {version}")

index_html = read("index.html")
ui = UiContractParser()
ui.feed(index_html)

require(ui.body_attrs.get("data-app") == "ailovanta-chat", "index.html must declare data-app=ailovanta-chat")
require(ui.body_attrs.get("data-guest-mode") == "true", "guest mode must remain enabled")
require(ui.body_attrs.get("data-login-required") == "false", "first-use path must not require login")
require(ui.body_attrs.get("data-payment-required") == "false", "first-use path must not require payment")
require(ui.body_attrs.get("data-wallet-required") == "false", "first-use path must not require wallet")

required_ids = {
    "conversationList",
    "guestBox",
    "messages",
    "prompt",
    "send",
    "copyChat",
    "clear",
    "deleteChat",
    "clearGuestData",
    "apiStatus",
    "apiDot",
    "modelLabel",
    "contextLabel",
    "chatStatus",
    "newChat",
    "refreshChats",
}
missing_ids = required_ids - ui.ids
require(not missing_ids, f"index.html missing required ids: {sorted(missing_ids)}")

required_classes = {
    "app",
    "sidebar",
    "main",
    "topbar",
    "messages",
    "composer",
    "conversationList",
    "bubble",
    "avatar",
}
missing_classes = required_classes - ui.classes
require(not missing_classes, f"index.html missing required classes: {sorted(missing_classes)}")

required_regions = {
    "conversation-sidebar",
    "conversation-list",
    "guest-session",
    "chat-main",
    "status-bar",
    "message-stream",
    "composer-wrap",
    "composer",
    "api-status",
}
missing_regions = required_regions - ui.data_regions
require(not missing_regions, f"index.html missing data-region contracts: {sorted(missing_regions)}")

required_actions = {
    "new-chat",
    "refresh-conversations",
    "reset-guest",
    "clear-guest-data",
    "copy-chat",
    "clear-view",
    "delete-chat",
    "send-message",
}
missing_actions = required_actions - ui.data_actions
require(not missing_actions, f"index.html missing data-action contracts: {sorted(missing_actions)}")

frontend_contract_markers = [
    "/ailovanta/v1/chat",
    "/ailovanta/v1/conversations",
    "context_messages_used",
    "guest_id",
    "markdownLite",
    "navigator.clipboard.writeText",
    "localStorage",
]
for marker in frontend_contract_markers:
    require(marker in index_html, f"index.html missing frontend contract marker: {marker}")

checks = {
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
    "docs/UI_VALIDATION_CONTRACT.md": ["data-guest-mode", "data-login-required", "data-region", "data-action"],
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
    text = read(rel)
    for marker in markers:
        require(marker in text, f"missing marker {marker} in {rel}")

print("Ailovanta validation passed.")
