from pathlib import Path

root = Path(__file__).resolve().parent
paths = {
    "index": root / "index.html",
    "dashboard": root / "dashboard.html",
    "readme": root / "README.md",
    "brand": root / "BRAND.md",
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
    "deployment_doc": root / "docs" / "DEPLOYMENT.md",
    "private_core_doc": root / "PRIVATE_CORE.md",
    "tests": root / "tests" / "test_api_contract.py",
    "health_tests": root / "tests" / "test_health_ready.py",
    "workflow": root / ".github" / "workflows" / "validate.yml",
    "requirements": root / "requirements.txt",
    "env_example": root / ".env.example",
}

for path in paths.values():
    assert path.exists(), f"missing file: {path.relative_to(root)}"

html = paths["index"].read_text(encoding="utf-8")
for marker in [
    "Ailovanta",
    "AI powered by the world's distributed compute.",
    "Ailovanta Node",
    "API Skeleton",
    "Training Simulator",
    "Ailovanta AI Demo",
]:
    assert marker in html, f"missing html marker: {marker}"

for banned in ["Open GPU Privacy AI", "OpenGPU Privacy AI", "NodeX AI", "Nodexa", "ManyMind AI"]:
    assert banned not in html, f"unexpected old brand in index.html: {banned}"

readme_text = paths["readme"].read_text(encoding="utf-8")
for marker in ["# Ailovanta", "ailovanta.git", "ailovanta-core.git", "Train, run, and validate AI"]:
    assert marker in readme_text, f"missing README marker: {marker}"

brand_text = paths["brand"].read_text(encoding="utf-8")
for marker in ["Ailovanta", "Ailovanta Core", "H-SwarmTrain", "ailovanta.git", "ailovanta-core.git"]:
    assert marker in brand_text, f"missing brand marker: {marker}"

api_text = paths["api"].read_text(encoding="utf-8")
for marker in [
    "FastAPI",
    "Ailovanta API",
    "SchedulerStore",
    "TrainingPlanner",
    "VerificationEngine",
    "/health",
    "/ready",
    "/training/jobs",
    "/models/versions",
    "/dashboard/summary",
    "/ai/chat",
]:
    assert marker in api_text, f"missing api marker: {marker}"

health_text = paths["health"].read_text(encoding="utf-8")
for marker in ["HealthStatus", "ailovanta-api", "get_health", "uptime_seconds"]:
    assert marker in health_text, f"missing health marker: {marker}"

storage_text = paths["storage"].read_text(encoding="utf-8")
for marker in ["SchedulerStore", "model_versions", "enqueue_job", "list_jobs", "register_model_version", "list_model_versions"]:
    assert marker in storage_text, f"missing storage marker: {marker}"

training_text = paths["training"].read_text(encoding="utf-8")
for marker in ["TrainingPlanner", "TrainingJobSpec", "ModelVersionSpec", "rag_import", "lora_micro"]:
    assert marker in training_text, f"missing training marker: {marker}"

verification_text = paths["verification"].read_text(encoding="utf-8")
for marker in ["VerificationEngine", "VerificationResult", "score_result"]:
    assert marker in verification_text, f"missing verification marker: {marker}"

client_text = paths["node_client"].read_text(encoding="utf-8")
for marker in ["ResourceGuard", "JobRunner", "request_with_retry", "setup_logging", "worker_loop"]:
    assert marker in client_text, f"missing node client marker: {marker}"

for text_path in [paths["dashboard"], paths["deployment_doc"], paths["private_core_doc"]]:
    text = text_path.read_text(encoding="utf-8")
    assert "Ailovanta" in text or "ailovanta" in text, f"missing Ailovanta marker in {text_path.relative_to(root)}"

workflow_text = paths["workflow"].read_text(encoding="utf-8")
for marker in ["pip install -r requirements.txt", "python validate.py", "python -m pytest -q"]:
    assert marker in workflow_text, f"missing workflow marker: {marker}"

assert "fastapi" in paths["requirements"].read_text(encoding="utf-8")
assert "pytest" in paths["requirements"].read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in paths["env_example"].read_text(encoding="utf-8")
assert html.count("<section") >= 7, "expected focused product sections"

print("Ailovanta validation passed.")
