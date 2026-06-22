from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"
api = root / "api" / "main.py"
storage = root / "api" / "storage.py"
ollama = root / "api" / "ollama_adapter.py"
memory = root / "api" / "memory_store.py"
node_client = root / "node_client" / "client.py"
node_device = root / "node_client" / "device.py"
resource_guard = root / "node_client" / "resource_guard.py"
job_runner = root / "node_client" / "job_runner.py"
scheduler_doc = root / "docs" / "SCHEDULER.md"
node_doc = root / "docs" / "NODE_CLIENT.md"
runtime_doc = root / "docs" / "LOCAL_RUNTIME.md"
ollama_doc = root / "docs" / "OLLAMA.md"
requirements = root / "requirements.txt"
env_example = root / ".env.example"

for path in [
    index,
    readme,
    api,
    storage,
    ollama,
    memory,
    node_client,
    node_device,
    resource_guard,
    job_runner,
    scheduler_doc,
    node_doc,
    runtime_doc,
    ollama_doc,
    requirements,
    env_example,
]:
    assert path.exists(), f"missing file: {path.relative_to(root)}"

html = index.read_text(encoding="utf-8")
for marker in [
    "Open GPU Privacy AI",
    "Run a node. Use private AI for free.",
    "Node Client",
    "API Skeleton",
    "Protocol",
    "Pricing",
    "Waitlist",
    "Training Simulator",
    "Robot Memory",
]:
    assert marker in html, f"missing html marker: {marker}"

api_text = api.read_text(encoding="utf-8")
for marker in ["FastAPI", "SchedulerStore", "OllamaAdapter", "MemoryStore", "/nodes/register", "/jobs/next", "/ai/chat", "/memory"]:
    assert marker in api_text, f"missing api marker: {marker}"

storage_text = storage.read_text(encoding="utf-8")
for marker in ["SchedulerStore", "sqlite3", "register_node", "next_job", "submit_result", "status"]:
    assert marker in storage_text, f"missing storage marker: {marker}"

client_text = node_client.read_text(encoding="utf-8")
for marker in ["ResourceGuard", "JobRunner", "request_with_retry", "setup_logging", "worker_loop"]:
    assert marker in client_text, f"missing node client marker: {marker}"

assert "fastapi" in requirements.read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in env_example.read_text(encoding="utf-8")
assert html.count("<section") >= 8, "expected v0.3+ product sections"

print("Validation passed.")
