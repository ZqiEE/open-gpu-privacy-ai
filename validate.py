from pathlib import Path

root = Path(__file__).resolve().parent
paths = {
    "index": root / "index.html",
    "dashboard": root / "dashboard.html",
    "readme": root / "README.md",
    "version": root / "VERSION",
    "brand": root / "BRAND.md",
    "contributing": root / "CONTRIBUTING.md",
    "api": root / "api" / "main.py",
    "runtime_router": root / "api" / "runtime_router.py",
    "runtime_store": root / "api" / "runtime_store.py",
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
    "runtime_demo_script": root / "scripts" / "demo_runtime_flow.py",
    "deployment_doc": root / "docs" / "DEPLOYMENT.md",
    "runtime_demo_doc": root / "docs" / "RUNTIME_DEMO.md",
    "status_doc": root / "docs" / "PROJECT_STATUS.md",
    "launch_doc": root / "docs" / "PUBLIC_LAUNCH_CHECKLIST.md",
    "repo_settings_doc": root / "docs" / "REPOSITORY_SETTINGS.md",
    "technical_doc": root / "docs" / "TECHNICAL_OVERVIEW.md",
    "runtime_arch_doc": root / "docs" / "MODEL_RUNTIME_ARCHITECTURE.md",
    "integration_doc": root / "docs" / "CORE_INTEGRATION_PLAN.md",
    "changelog": root / "docs" / "CHANGELOG.md",
    "private_core_doc": root / "PRIVATE_CORE.md",
    "dockerfile": root / "Dockerfile",
    "tests": root / "tests" / "test_api_contract.py",
    "health_tests": root / "tests" / "test_health_ready.py",
    "workflow": root / ".github" / "workflows" / "validate.yml",
    "pr_template": root / ".github" / "pull_request_template.md",
    "bug_template": root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml",
    "feature_template": root / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml",
    "requirements": root / "requirements.txt",
    "env_example": root / ".env.example",
}

for path in paths.values():
    assert path.exists(), f"missing file: {path.relative_to(root)}"

version_text = paths["version"].read_text(encoding="utf-8").strip()
assert version_text == "1.5.0-runtime-store", f"unexpected version: {version_text}"

html = paths["index"].read_text(encoding="utf-8")
for marker in ["Ailovanta", "AI powered by the world's distributed compute.", "Ailovanta Node", "API Skeleton", "Training Simulator", "Ailovanta AI Demo"]:
    assert marker in html, f"missing html marker: {marker}"

readme_text = paths["readme"].read_text(encoding="utf-8")
for marker in ["# Ailovanta", "ailovanta.git", "ailovanta-core.git", "demo_runtime_flow.py", "RUNTIME_DEMO.md", "MODEL_RUNTIME_ARCHITECTURE.md", "CORE_INTEGRATION_PLAN.md", "PROJECT_STATUS.md", "Train, run, and validate AI"]:
    assert marker in readme_text, f"missing README marker: {marker}"

brand_text = paths["brand"].read_text(encoding="utf-8")
for marker in ["Ailovanta", "Ailovanta Core", "H-SwarmTrain", "ailovanta.git", "ailovanta-core.git"]:
    assert marker in brand_text, f"missing brand marker: {marker}"

contributing_text = paths["contributing"].read_text(encoding="utf-8")
for marker in ["Contributing to Ailovanta", "python validate.py", "python -m pytest -q"]:
    assert marker in contributing_text, f"missing contributing marker: {marker}"

runtime_demo_doc = paths["runtime_demo_doc"].read_text(encoding="utf-8")
for marker in ["Runtime Demo", "demo_runtime_flow.py", "model manifest", "runtime node", "route request"]:
    assert marker in runtime_demo_doc, f"missing runtime demo doc marker: {marker}"

runtime_demo_script = paths["runtime_demo_script"].read_text(encoding="utf-8")
for marker in ["/runtime/models/register", "/runtime/nodes/register", "/runtime/route", "/runtime/assignments"]:
    assert marker in runtime_demo_script, f"missing runtime demo script marker: {marker}"

status_text = paths["status_doc"].read_text(encoding="utf-8")
for marker in ["Current stage", "Done in the public repository", "Not done yet", "Safe public claim"]:
    assert marker in status_text, f"missing status marker: {marker}"

launch_text = paths["launch_doc"].read_text(encoding="utf-8")
for marker in ["Public Launch Checklist", "python validate.py", "Safe public claim"]:
    assert marker in launch_text, f"missing launch checklist marker: {marker}"

repo_settings_text = paths["repo_settings_doc"].read_text(encoding="utf-8")
for marker in ["Repository Settings", "ailovanta", "Branch protection", "Ailovanta CI"]:
    assert marker in repo_settings_text, f"missing repo settings marker: {marker}"

technical_text = paths["technical_doc"].read_text(encoding="utf-8")
for marker in ["Ailovanta Technical Overview", "Model runtime architecture", "Job lifecycle", "Training lifecycle", "Public/core split"]:
    assert marker in technical_text, f"missing technical overview marker: {marker}"

runtime_text = paths["runtime_arch_doc"].read_text(encoding="utf-8")
for marker in ["Model Runtime Architecture", "Access Router", "Runtime Pool", "warm runtime", "verified model chunks", "Do not centralize the model"]:
    assert marker in runtime_text, f"missing model runtime marker: {marker}"

integration_text = paths["integration_doc"].read_text(encoding="utf-8")
for marker in ["Core Integration Plan", "Runtime pool interface", "Access Router", "Phase 1", "Phase 2", "Phase 3", "Phase 4"]:
    assert marker in integration_text, f"missing integration plan marker: {marker}"

changelog_text = paths["changelog"].read_text(encoding="utf-8")
for marker in ["v1.5 Runtime Store MVP", "v1.4 Runtime Router MVP", "1.5.0-runtime-store"]:
    assert marker in changelog_text, f"missing changelog marker: {marker}"

api_text = paths["api"].read_text(encoding="utf-8")
for marker in ["FastAPI", "FileResponse", "Ailovanta API", "RuntimeStore", "RuntimeModelRegister", "RuntimeNodeRegister", "RuntimeRouteRequest", "/runtime/models/register", "/runtime/nodes/register", "/runtime/status", "/runtime/assignments", "/runtime/route", "/app", "/dashboard", "/health", "/ready", "/network/status", "/verification/status", "/jobs/retry-failed", "/jobs/requeue-stale", "/training/jobs", "/models/versions", "/dashboard/summary", "/ai/chat"]:
    assert marker in api_text, f"missing api marker: {marker}"

router_text = paths["runtime_router"].read_text(encoding="utf-8")
for marker in ["ModelManifest", "RuntimeNodeProfile", "RuntimeRequest", "RuntimeAssignment", "RuntimeRegistry", "has_warm_model", "privacy_level"]:
    assert marker in router_text, f"missing runtime router marker: {marker}"

store_text = paths["runtime_store"].read_text(encoding="utf-8")
for marker in ["RuntimeStore", "runtime_models", "runtime_nodes", "runtime_assignments", "list_assignments", "RuntimeRegistry"]:
    assert marker in store_text, f"missing runtime store marker: {marker}"

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
for marker in ["ResourceGuard", "JobRunner", "request_with_retry", "setup_logging", "worker_loop", "Ailovanta"]:
    assert marker in client_text, f"missing node client marker: {marker}"

test_text = paths["tests"].read_text(encoding="utf-8")
for marker in ["test_runtime_router_prefers_warm_verified_runtime", "test_private_runtime_routes_only_to_trusted_pool", "runtime_registry.clear", "/runtime/route"]:
    assert marker in test_text, f"missing runtime test marker: {marker}"

for text_path in [paths["dashboard"], paths["deployment_doc"], paths["private_core_doc"]]:
    text = text_path.read_text(encoding="utf-8")
    assert "Ailovanta" in text or "ailovanta" in text, f"missing Ailovanta marker in {text_path.relative_to(root)}"

docker_text = paths["dockerfile"].read_text(encoding="utf-8")
for marker in ["dashboard.html", "BRAND.md", "SECURITY_BOUNDARY.md", "PRIVATE_CORE.md"]:
    assert marker in docker_text, f"missing Dockerfile marker: {marker}"

workflow_text = paths["workflow"].read_text(encoding="utf-8")
for marker in ["Ailovanta CI", "pip install -r requirements.txt", "python validate.py", "python -m pytest -q"]:
    assert marker in workflow_text, f"missing workflow marker: {marker}"

pr_text = paths["pr_template"].read_text(encoding="utf-8")
for marker in ["Ailovanta Pull Request", "Public/private boundary", "python validate.py"]:
    assert marker in pr_text, f"missing PR template marker: {marker}"

for template_key in ["bug_template", "feature_template"]:
    template_text = paths[template_key].read_text(encoding="utf-8")
    assert "Ailovanta" in template_text, f"missing Ailovanta marker in {template_key}"

assert "fastapi" in paths["requirements"].read_text(encoding="utf-8")
assert "pytest" in paths["requirements"].read_text(encoding="utf-8")
assert "OLLAMA_MODEL" in paths["env_example"].read_text(encoding="utf-8")
assert html.count("<section") >= 7, "expected focused product sections"

print("Ailovanta validation passed.")
