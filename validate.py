from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
readme = root / "README.md"
api = root / "api" / "main.py"
storage = root / "api" / "storage.py"
training = root / "api" / "training.py"
verification = root / "api" / "verification.py"
ollama = root / "api" / "ollama_adapter.py"
memory = root / "api" / "memory_store.py"
node_client = root / "node_client" / "client.py"
node_device = root / "node_client" / "device.py"
resource_guard = root / "node_client" / "resource_guard.py"
job_runner = root / "node_client" / "job_runner.py"
training_doc = root / "docs" / "TRAINING.md"
scheduler_doc = root / "docs" / "SCHEDULER.md"
verification_doc = root / "docs" / "VERIFICATION.md"
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
    training,
    verification,
    ollama,
    memory,
    node_client,
    node_device,
    resource_guard,
    job_runner,
    training_doc,
    scheduler_doc,
    verification_doc,
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
for marker in [
    "FastAPI",
    "SchedulerStore",
    "TrainingPlanner",
    "VerificationEngine",
    "/training/jobs",
    "/models/versions",
    "/jobs/retry-failed",
    "/verification/status",
]:
    assert marker in api_text, f"missing api marker: {marker}"

storage_text = storage.read_text(encoding="utf-8")
for marker in [
    "SchedulerStore",
    "model_versions",
    "enqueue_job",
    "list_jobs",
    "register_model_version",
    "list_model_versions",
]:
    assert marker in storage_text, f"missing storage marker: {marker}"

training_text = training.read_text(encoding="utf-8")
for marker in ["TrainingPlanner", "TrainingJobSpec", "ModelVersionSpec", "rag_import", "lora_micro"]:
    assert marker in training_text, f"missing training marker: {marker}"

verification_text = verification.read_text(encoding="utf-8")
for marker in ["VerificationEngine", "VerificationResult", "score_result"]:
    assert marker in verification_text, f"missing verification marker: {marker}"

client_text = node_client.read_text(encoding="utf-8")
for marker in ["ResourceGuard", "JobRunner", "request_with_retry", "setup_logging", "worker_loop"]:
    assert marker in client_text, f"missing node client marker: {marker}"

assert "fastapi" in requirements.read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in env_example.read_text(encoding="utf-8")
assert html.count("<section") >= 8, "expected v0.3+ product sections"

print("Validation passed.")
