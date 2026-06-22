from pathlib import Path

root = Path(__file__).resolve().parent
paths = {
    "index": root / "index.html",
    "readme": root / "README.md",
    "api": root / "api" / "main.py",
    "health": root / "api" / "health.py",
    "storage": root / "api" / "storage.py",
    "training": root / "api" / "training.py",
    "verification": root / "api" / "verification.py",
    "ollama": root / "api" / "ollama_adapter.py",
    "memory": root / "api" / "memory_store.py",
    "node_client": root / "node_client" / "client.py",
    "node_device": root / "node_client" / "device.py",
    "resource_guard": root / "node_client" / "resource_guard.py",
    "job_runner": root / "node_client" / "job_runner.py",
    "training_doc": root / "docs" / "TRAINING.md",
    "scheduler_doc": root / "docs" / "SCHEDULER.md",
    "verification_doc": root / "docs" / "VERIFICATION.md",
    "node_doc": root / "docs" / "NODE_CLIENT.md",
    "runtime_doc": root / "docs" / "LOCAL_RUNTIME.md",
    "ollama_doc": root / "docs" / "OLLAMA.md",
    "api_doc": root / "docs" / "API.md",
    "deployment_doc": root / "docs" / "DEPLOYMENT.md",
    "security_doc": root / "docs" / "SECURITY.md",
    "operations_doc": root / "docs" / "OPERATIONS.md",
    "handoff_doc": root / "docs" / "DEVELOPER_HANDOFF.md",
    "changelog_doc": root / "docs" / "CHANGELOG.md",
    "tests": root / "tests" / "test_api_contract.py",
    "health_tests": root / "tests" / "test_health_ready.py",
    "smoke": root / "scripts" / "smoke_api.py",
    "maintenance": root / "scripts" / "queue_maintenance.py",
    "demo_training": root / "scripts" / "demo_training_flow.py",
    "dockerfile": root / "Dockerfile",
    "compose": root / "docker-compose.yml",
    "makefile": root / "Makefile",
    "workflow": root / ".github" / "workflows" / "validate.yml",
    "requirements": root / "requirements.txt",
    "env_example": root / ".env.example",
}

for path in paths.values():
    assert path.exists(), f"missing file: {path.relative_to(root)}"

html = paths["index"].read_text(encoding="utf-8")
for marker in ["Open GPU Privacy AI", "Run a node. Use private AI for free.", "Node Client", "API Skeleton", "Protocol", "Pricing", "Waitlist", "Training Simulator", "Private AI Demo"]:
    assert marker in html, f"missing html marker: {marker}"

for banned in ["Robot", "robot"]:
    assert banned not in html, f"unexpected robot scope in index.html: {banned}"

readme_text = paths["readme"].read_text(encoding="utf-8")
for marker in ["v1.0 Engineering Pack", "Dockerfile", "tests/test_api_contract.py", "docs/API.md", "docs/SECURITY.md"]:
    assert marker in readme_text, f"missing README marker: {marker}"
for banned in ["Robot", "robot"]:
    assert banned not in readme_text, f"unexpected robot scope in README.md: {banned}"

api_text = paths["api"].read_text(encoding="utf-8")
for marker in ["FastAPI", "SchedulerStore", "TrainingPlanner", "VerificationEngine", "/health", "/ready", "/training/jobs", "/models/versions", "/jobs/retry-failed", "/verification/status"]:
    assert marker in api_text, f"missing api marker: {marker}"

health_text = paths["health"].read_text(encoding="utf-8")
for marker in ["HealthStatus", "get_health", "uptime_seconds"]:
    assert marker in health_text, f"missing health marker: {marker}"

storage_text = paths["storage"].read_text(encoding="utf-8")
for marker in ["SchedulerStore", "model_versions", "enqueue_job", "list_jobs", "register_model_version", "list_model_versions"]:
    assert marker in storage_text, f"missing storage marker: {marker}"

training_text = paths["training"].read_text(encoding="utf-8")
for marker in ["TrainingPlanner", "TrainingJobSpec", "ModelVersionSpec", "rag_import", "lora_micro", "private_memory_tune"]:
    assert marker in training_text, f"missing training marker: {marker}"
assert "robot_memory_tune" not in training_text

verification_text = paths["verification"].read_text(encoding="utf-8")
for marker in ["VerificationEngine", "VerificationResult", "score_result"]:
    assert marker in verification_text, f"missing verification marker: {marker}"

client_text = paths["node_client"].read_text(encoding="utf-8")
for marker in ["ResourceGuard", "JobRunner", "request_with_retry", "setup_logging", "worker_loop"]:
    assert marker in client_text, f"missing node client marker: {marker}"

for script_name in ["smoke", "maintenance", "demo_training"]:
    script_text = paths[script_name].read_text(encoding="utf-8")
    assert "httpx" in script_text, f"missing httpx usage in {script_name}"

workflow_text = paths["workflow"].read_text(encoding="utf-8")
for marker in ["pip install -r requirements.txt", "python validate.py", "python -m pytest -q"]:
    assert marker in workflow_text, f"missing workflow marker: {marker}"

assert "fastapi" in paths["requirements"].read_text(encoding="utf-8")
assert "pytest" in paths["requirements"].read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in paths["env_example"].read_text(encoding="utf-8")
assert html.count("<section") >= 7, "expected focused product sections"

print("Validation passed.")
