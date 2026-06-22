from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"
api = root / "api" / "main.py"
node_client = root / "node_client" / "client.py"
runtime_doc = root / "docs" / "LOCAL_RUNTIME.md"
requirements = root / "requirements.txt"

for path in [index, readme, api, node_client, runtime_doc, requirements]:
    assert path.exists(), f"missing file: {path.relative_to(root)}"

html = index.read_text(encoding="utf-8")
required_html = [
    "Open GPU Privacy AI",
    "Run a node. Use private AI for free.",
    "Node Client",
    "API Skeleton",
    "Protocol",
    "Pricing",
    "Waitlist",
    "Training Simulator",
    "Robot Memory",
]
for marker in required_html:
    assert marker in html, f"missing html marker: {marker}"

api_text = api.read_text(encoding="utf-8")
for marker in ["FastAPI", "/nodes/register", "/jobs/next", "/ai/chat", "/network/status"]:
    assert marker in api_text, f"missing api marker: {marker}"

client_text = node_client.read_text(encoding="utf-8")
for marker in ["register_node", "heartbeat", "worker_loop", "psutil"]:
    assert marker in client_text, f"missing node client marker: {marker}"

assert "fastapi" in requirements.read_text(encoding="utf-8")
assert html.count("<section") >= 8, "expected v0.3+ product sections"

print("Validation passed.")
