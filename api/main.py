from __future__ import annotations

from pathlib import Path
import os
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from api.ailovanta_native import AilovantaRunRequest, build_run_result
from api.auth_store import AuthStore
from api.conversation_context import build_chat_context
from api.conversation_store import ConversationStore
from api.dashboard import DashboardService
from api.github_auth import GitHubAuthConfigError, build_github_login_url, exchange_code_for_token, fetch_github_profile
from api.gpu_probe import detect_gpu
from api.health import get_health
from api.memory_store import MemoryStore
from api.node_security import require_token
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable
from api.owned_runtime_dashboard import OwnedRuntimeDashboard
from api.openai_compat import ChatCompletionRequest, build_chat_completion_response, extract_user_prompt
from api.reputation import ReputationService
from api.runtime_router import ModelManifest, RuntimeNodeProfile, RuntimeRequest
from api.runtime_store import RuntimeStore
from api.store_factory import create_scheduler_store, store_status
from api.training import TrainingKind, TrainingPlanner
from api.training_worker_result_validator import TrainingWorkerResultStore, validate_training_worker_result
from api.training_job_export import export_training_job
from api.training_pipeline import run_training_pipeline
from api.usage_store import UsageStore
from api.verification import VerificationEngine
from api.reputation_ops import ReputationOps
from api.replica_repair_api import router as replica_repair_router
from api.worker_result_validator import WorkerResultValidationStore, validate_worker_result

APP_VERSION = "1.12.0"
TRAINING_JOB_TYPES = {"rag_import", "lora_micro", "evaluation_batch", "private_memory_tune"}
BASE_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(title="Ailovanta API", version=APP_VERSION)
app.include_router(replica_repair_router)

auth_store = AuthStore()
store = create_scheduler_store()
usage_store = UsageStore()
dashboard = DashboardService(store)
reputation = ReputationService(store)
memories = MemoryStore()
ollama = OllamaAdapter()
verifier = VerificationEngine()
training = TrainingPlanner()
runtime_registry = RuntimeStore()
conversations = ConversationStore()


class NodeRegister(BaseModel):
    node_id: str | None = None
    device_name: str
    cpu_threads: int = Field(ge=1)
    memory_gb: float = Field(ge=0)
    has_gpu: bool = False
    gpu_name: str | None = None
    contribution_percent: int = Field(default=30, ge=1, le=90)


class Heartbeat(BaseModel):
    node_id: str
    status: Literal["online", "busy", "idle", "offline"] = "online"


class JobResult(BaseModel):
    node_id: str
    job_id: str
    status: Literal["ok", "failed"]
    output_summary: str


class TrainingJobRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    kind: TrainingKind
    name: str
    dataset_uri: str
    base_model: str = "qwen2.5:3b"
    max_steps: int = Field(default=100, ge=1, le=10000)
    notes: str = ""
    real: bool = False
    use_transformers: bool = False
    peft: bool = False
    lora: bool = False
    qlora: bool = False
    requires_gpu: bool = False
    allow_lightweight_fallback: bool = False
    priority: int | None = Field(default=None, ge=0, le=1000)
    min_memory_gb: float | None = Field(default=None, ge=0)
    min_cpu_threads: int | None = Field(default=None, ge=0)
    output_dir: str | None = None
    batch_size: int | None = Field(default=None, ge=1)
    gradient_accumulation_steps: int | None = Field(default=None, ge=1)
    learning_rate: float | None = Field(default=None, gt=0)
    max_length: int | None = Field(default=None, ge=1)
    target_modules: list[str] | None = None


class ModelVersionRequest(BaseModel):
    name: str
    base_model: str
    source_job_id: str
    notes: str = ""


class TrainingPipelineRequest(BaseModel):
    job_id: str
    core_path: str | None = None
    work_dir: str = "runtime_data/training_pipeline"


class MemoryAddRequest(BaseModel):
    owner: str = "local"
    text: str
    source: str = "manual"
    private: bool = True


class TrainingPlanRequest(BaseModel):
    kind: TrainingKind
    owner: str = "local"
    dataset_uri: str = "memory://local"
    base_model: str = "qwen2.5:3b"
    budget_steps: int = Field(default=50, ge=1, le=10000)
    private: bool = True


class NativeChatRequest(BaseModel):
    prompt: str
    user_id: str = "local"
    conversation_id: str | None = None
    title: str = "New chat"
    model_id: str = "ailovanta-local"
    version: str = "local"
    use_runtime_router: bool = False


class UsageEventRequest(BaseModel):
    user_id: str = "local"
    event_type: str
    quantity: float = Field(default=1.0, ge=0)
    source: str = "api"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeModelRegister(BaseModel):
    model_id: str
    version: str
    manifest_hash: str
    privacy_level: Literal["public", "protected", "private"] = "public"
    min_gpu_memory_gb: float = Field(default=0.0, ge=0)
    allowed_pools: list[Literal["cpu_pool", "small_gpu_pool", "large_gpu_pool", "storage_pool", "validator_pool", "trusted_runtime_pool", "enterprise_pool"]] = Field(default_factory=lambda: ["small_gpu_pool", "large_gpu_pool", "enterprise_pool"])
    quantization: str = "unknown"
    context_length: int = Field(default=4096, ge=1)
    adapter_compatible: bool = True
    status: str = "active"


class RuntimeNodeRegister(BaseModel):
    runtime_id: str
    node_id: str
    pool: Literal["cpu_pool", "small_gpu_pool", "large_gpu_pool", "storage_pool", "validator_pool", "trusted_runtime_pool", "enterprise_pool"]
    region: str = "global"
    status: str = "online"
    gpu_memory_gb: float = Field(default=0.0, ge=0)
    available_gpu_memory_gb: float = Field(default=0.0, ge=0)
    trust_score: float = Field(default=0.5, ge=0, le=1)
    current_load: float = Field(default=0.0, ge=0, le=1)
    price_per_1k_tokens: float = Field(default=0.0, ge=0)
    latency_ms: int = Field(default=1000, ge=1)
    supported_engines: list[str] = Field(default_factory=list)
    cached_models: list[str] = Field(default_factory=list)
    cached_adapters: list[str] = Field(default_factory=list)


class RuntimeRouteRequest(BaseModel):
    request_id: str
    model_id: str
    version: str
    task_type: Literal["chat_completion", "embedding", "rerank", "batch", "training", "validation"] = "chat_completion"
    privacy_level: Literal["public", "protected", "private"] = "public"
    latency_target_ms: int = Field(default=2000, ge=1)
    max_price_per_1k_tokens: float = Field(default=0.1, ge=0)
    region_hint: str = "auto"
    required_context_length: int = Field(default=4096, ge=1)
    required_adapter: str | None = None
    verification_required: bool = True


class WorkerResultValidationRequest(BaseModel):
    worker_result: dict[str, Any]
    artifact_manifest: dict[str, Any] | None = None
    sample_size: int = Field(default=2, ge=0, le=32)
    apply_reputation: bool = True


class TrainingWorkerResultValidationRequest(BaseModel):
    worker_result: dict[str, Any]


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    return authorization.removeprefix("Bearer ").strip()


def node_guard(token: str | None) -> None:
    try:
        require_token(token)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def answer_with_ollama(prompt: str, context_messages: list[dict] | None = None) -> tuple[str, str]:
    try:
        if context_messages is not None:
            return ollama.chat_messages(context_messages, "open", []), "ollama"
        return ollama.chat(prompt, "open", []), "ollama"
    except OllamaUnavailable:
        return "Ailovanta local fallback: connect Ollama or a registered runtime to enable real model responses.", "fallback"


def prefer_owned_chat() -> bool:
    return os.getenv("AILOVANTA_PREFER_OWNED_MODEL", "true").lower() not in {"0", "false", "no", "off"}


def require_owned_chat() -> bool:
    return os.getenv("AILOVANTA_REQUIRE_OWNED_MODEL", "").lower() in {"1", "true", "yes", "on"}


def owned_model_target(model_id: str, version: str) -> tuple[str, str]:
    owned_model_id = model_id if model_id != "ailovanta-local" else os.getenv("AILOVANTA_OWNED_MODEL_ID", "ailovanta-owned")
    owned_version = version if version != "local" else os.getenv("AILOVANTA_OWNED_MODEL_VERSION", "candidate")
    return owned_model_id, owned_version


def worker_validation_store() -> WorkerResultValidationStore:
    return WorkerResultValidationStore(os.getenv("AILOVANTA_WORKER_VALIDATION_PATH", "runtime_data/worker_result_validations.sqlite3"))


def training_worker_result_store() -> TrainingWorkerResultStore:
    return TrainingWorkerResultStore(os.getenv("AILOVANTA_TRAINING_WORKER_RESULT_PATH", "runtime_data/training_worker_result_receipts.sqlite3"))


def worker_reputation_store() -> ReputationOps:
    return ReputationOps(os.getenv("AILOVANTA_REPUTATION_PATH", str(store.path)))


def owned_runtime_dashboard() -> OwnedRuntimeDashboard:
    return OwnedRuntimeDashboard(runtime_registry, worker_validation_store(), worker_reputation_store())


def artifact_manifest_from_worker_result(worker_result: dict[str, Any]) -> dict[str, Any] | None:
    provenance = worker_result.get("validation_provenance") if isinstance(worker_result.get("validation_provenance"), dict) else {}
    binding = worker_result.get("artifact_binding") if isinstance(worker_result.get("artifact_binding"), dict) else {}
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    candidates = [
        worker_result.get("artifact_manifest"),
        provenance.get("artifact_manifest"),
        metadata.get("artifact_manifest"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate
    return None


@app.get("/")
def root() -> dict:
    return {"name": "Ailovanta", "version": APP_VERSION, "tagline": "AI powered by the world's distributed compute.", "app": "/app", "dashboard": "/dashboard", "admin": "/admin-secure", "docs": "/docs", "auth": "/auth/github/login", "ailovanta_native": "/ailovanta/v1/run", "ailovanta_chat": "/ailovanta/v1/chat", "compatibility_chat": "/v1/chat/completions", "scheduler": store_status(store), "runtime": runtime_registry.status(), "conversations": conversations.status(), "auth_status": auth_store.status()}


@app.get("/app")
def public_app() -> FileResponse:
    path = BASE_DIR / "index.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(path)


@app.get("/dashboard")
def dashboard_app() -> FileResponse:
    path = BASE_DIR / "dashboard.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    return FileResponse(path)


@app.get("/auth/github/login")
def github_login() -> dict:
    state = auth_store.create_state()
    try:
        login_url = build_github_login_url(state)
    except GitHubAuthConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"provider": "github", "login_url": login_url, "state": state}


@app.get("/auth/github/callback")
def github_callback(code: str, state: str) -> dict:
    if not auth_store.consume_state(state):
        raise HTTPException(status_code=400, detail="invalid or expired auth state")
    try:
        access_token = exchange_code_for_token(code)
        profile = fetch_github_profile(access_token)
    except GitHubAuthConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="GitHub login failed") from exc
    user = auth_store.upsert_github_user(profile)
    session = auth_store.create_session(user["id"])
    return {"user": user, "session": session}


@app.get("/auth/me")
def auth_me(authorization: str | None = Header(default=None)) -> dict:
    token = bearer_token(authorization)
    session = auth_store.get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="invalid or expired session")
    return {"user": auth_store.get_user(session["user_id"]), "session": session}


@app.post("/auth/logout")
def auth_logout(authorization: str | None = Header(default=None)) -> dict:
    return {"ok": auth_store.revoke_session(bearer_token(authorization))}


@app.get("/health")
def health() -> dict:
    return get_health(APP_VERSION)


@app.get("/local/gpu")
def local_gpu() -> dict:
    return detect_gpu()


@app.get("/ready")
def ready() -> dict:
    status = store_status(store)
    return {"ok": True, "scheduler_store": status["store"], "path": status.get("path") or status.get("database_url"), "redis": status.get("redis")}


@app.get("/network/status")
def network_status() -> dict:
    return store_status(store)


@app.get("/verification/status")
def verification_status() -> dict:
    status = store_status(store)
    return {"verifications": status["verifications"], "passed_verifications": status["passed_verifications"], "pass_rate": round(status["passed_verifications"] / status["verifications"], 3) if status["verifications"] else 0.0}


@app.get("/dashboard/summary")
def dashboard_summary() -> dict:
    return dashboard.summary()


@app.get("/dashboard/jobs")
def dashboard_jobs(limit: int = 20) -> dict:
    return dashboard.recent_jobs(limit=limit)


@app.get("/dashboard/models")
def dashboard_models(limit: int = 20) -> dict:
    return dashboard.model_versions(limit=limit)


@app.get("/dashboard/owned-runtime")
def dashboard_owned_runtime(limit: int = 20) -> dict:
    return owned_runtime_dashboard().summary(limit=limit)


@app.get("/reputation/leaderboard")
def reputation_leaderboard(limit: int = 20) -> dict:
    return reputation.leaderboard(limit=limit)


@app.get("/reputation/summary")
def reputation_summary() -> dict:
    return reputation.summary()


@app.post("/jobs/retry-failed")
def retry_failed_jobs(max_attempts: int = 3) -> dict:
    return store.retry_failed_jobs(max_attempts=max_attempts)


@app.post("/jobs/requeue-stale")
def requeue_stale_jobs(older_than_minutes: int = 30) -> dict:
    return store.requeue_stale_assigned(older_than_minutes=older_than_minutes)


@app.post("/nodes/register")
def register_node(body: NodeRegister, x_ailovanta_node_token: str | None = Header(default=None)) -> dict:
    node_guard(x_ailovanta_node_token)
    return store.register_node(body.model_dump())


@app.get("/nodes")
def list_nodes(limit: int = 50) -> dict:
    return {"nodes": store.list_nodes(limit=limit)}


@app.post("/nodes/heartbeat")
def heartbeat(body: Heartbeat, x_ailovanta_node_token: str | None = Header(default=None)) -> dict:
    node_guard(x_ailovanta_node_token)
    node = store.update_heartbeat(body.node_id, body.status)
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@app.get("/nodes/{node_id}")
def get_node(node_id: str) -> dict:
    node = store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@app.get("/nodes/{node_id}/route-preview")
def route_preview(node_id: str, limit: int = 20) -> dict:
    return store.queued_route_preview(node_id=node_id, limit=limit)


@app.get("/jobs")
def list_jobs(status: str | None = None, limit: int = 50) -> dict:
    return {"jobs": store.list_jobs(status=status, limit=limit)}


@app.post("/jobs")
def create_job(job_id: str, job_type: str, payload: dict) -> dict:
    return {"job": store.enqueue_job(job_id, job_type, payload)}


@app.get("/jobs/next")
@app.post("/jobs/next")
def next_job(node_id: str, x_ailovanta_node_token: str | None = Header(default=None)) -> dict:
    node_guard(x_ailovanta_node_token)
    job = store.next_job(node_id)
    if not job:
        raise HTTPException(status_code=404, detail="no matching job")
    return {"job": job}


@app.post("/jobs/result")
@app.post("/results")
def submit_result(body: JobResult, x_ailovanta_node_token: str | None = Header(default=None)) -> dict:
    node_guard(x_ailovanta_node_token)
    result = store.submit_result(body.model_dump())
    verification = verifier.verify(result)
    stored = store.record_verification(result, verification["score"], verification["passed"], verification["reason"])
    return {"ok": True, "result": result, "verification": stored}


@app.post("/training/jobs")
def create_training_job(body: TrainingJobRequest) -> dict:
    job_type = str(body.kind)
    if job_type not in TRAINING_JOB_TYPES:
        raise HTTPException(status_code=400, detail="unsupported training job type")
    job = store.enqueue_job("train_" + uuid4().hex[:12], job_type, body.model_dump())
    return {"ok": True, "job": job}


@app.get("/training/jobs")
def list_training_jobs(limit: int = 50) -> dict:
    return {"jobs": [job for job in store.list_jobs(limit=limit) if job["type"] in TRAINING_JOB_TYPES]}


@app.post("/training/jobs/{job_id}/export")
def export_training_job_route(job_id: str) -> dict:
    try:
        return {"ok": True, "export": export_training_job(job_id, store=store)}
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@app.post("/training/pipeline/run")
def run_training_pipeline_route(body: TrainingPipelineRequest) -> dict:
    try:
        return run_training_pipeline(body.job_id, core_path=body.core_path, work_dir=body.work_dir, store=store)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc


@app.post("/training/plan")
def plan_training(body: TrainingPlanRequest) -> dict:
    plan = training.plan(body.kind, body.owner, body.dataset_uri, body.base_model, body.budget_steps, body.private)
    return {"plan": plan.model_dump(), "job": store.enqueue_job(plan.job_id, plan.job_type, plan.model_dump())}


@app.post("/models/versions")
@app.post("/models")
def register_model_version(body: ModelVersionRequest) -> dict:
    model_id = f"model_{body.name.lower().replace(' ', '_')}_{body.source_job_id}"
    return {"model": store.register_model_version({"model_id": model_id, **body.model_dump()})}


@app.get("/models")
def list_model_versions(limit: int = 50) -> dict:
    return {"models": store.list_model_versions(limit=limit)}


@app.post("/memories")
def add_memory(body: MemoryAddRequest) -> dict:
    return memories.add(body.owner, body.text, body.source, body.private)


@app.get("/memories")
def list_memories(owner: str = "local") -> dict:
    return {"memories": memories.list(owner)}


@app.get("/memories/search")
def search_memories(q: str, owner: str = "local") -> dict:
    return {"matches": memories.search(owner, q)}


@app.post("/runtime/models/register")
@app.post("/runtime/models")
def register_runtime_model(body: RuntimeModelRegister) -> dict:
    return runtime_registry.register_model(ModelManifest(**body.model_dump()))


@app.get("/runtime/models")
def list_runtime_models() -> dict:
    return {"models": runtime_registry.list_models()}


@app.post("/runtime/nodes/register")
@app.post("/runtime/nodes")
def register_runtime_node(body: RuntimeNodeRegister) -> dict:
    return runtime_registry.register_runtime(RuntimeNodeProfile(**body.model_dump()))


@app.get("/runtime/nodes")
def list_runtime_nodes() -> dict:
    return {"nodes": runtime_registry.list_runtimes()}


@app.post("/runtime/route")
def runtime_route(body: RuntimeRouteRequest) -> dict:
    return runtime_registry.route(RuntimeRequest(**body.model_dump()))


@app.get("/runtime/assignments")
def runtime_assignments(limit: int = 50) -> dict:
    return {"assignments": runtime_registry.list_assignments(limit=limit)}


@app.get("/runtime/status")
def runtime_status() -> dict:
    return runtime_registry.status()


@app.post("/worker-results/validate")
def validate_worker_result_route(body: WorkerResultValidationRequest) -> dict:
    return {
        "ok": True,
        "receipt": validate_worker_result(
            body.worker_result,
            artifact_manifest=body.artifact_manifest,
            sample_size=body.sample_size,
            store=worker_validation_store(),
            reputation=worker_reputation_store() if body.apply_reputation else None,
            apply_reputation=body.apply_reputation,
        ),
    }


@app.get("/worker-results/validations")
def list_worker_result_validations(node_id: str | None = None, limit: int = 100) -> dict:
    return {"receipts": worker_validation_store().list(node_id=node_id, limit=limit)}


@app.post("/training/worker-results/validate")
def validate_training_worker_result_route(body: TrainingWorkerResultValidationRequest) -> dict:
    return {
        "receipt": validate_training_worker_result(
            body.worker_result,
            store=training_worker_result_store(),
        )
    }


@app.get("/training/worker-results/validations")
def list_training_worker_result_validations(node_id: str | None = None, job_id: str | None = None, limit: int = 100) -> dict:
    return {"receipts": training_worker_result_store().list(node_id=node_id, job_id=job_id, limit=limit)}


@app.post("/ailovanta/v1/run")
def ailovanta_run(body: AilovantaRunRequest) -> dict:
    route = {"assigned": False, "reason": "runtime routing not requested"}
    if body.use_runtime_router:
        route = runtime_registry.route(RuntimeRequest(request_id=f"run-{uuid4().hex[:8]}", model_id=body.model_id, version=body.version, task_type=body.task_type, privacy_level=body.privacy_level, latency_target_ms=body.latency_target_ms, max_price_per_1k_tokens=body.max_price_per_1k_tokens, region_hint=body.region_hint, verification_required=body.verification_required))
    answer, source = answer_with_ollama(body.prompt)
    usage_store.record(body.user_id, "ailovanta.run", 1, source, {"model_id": body.model_id})
    return build_run_result(body, answer, source, route)


@app.post("/v1/chat/completions")
def chat_completions(body: ChatCompletionRequest) -> dict:
    prompt = extract_user_prompt(body.messages)
    answer, _source = answer_with_ollama(prompt)
    return build_chat_completion_response(body.model, answer, prompt)


@app.post("/ailovanta/v1/chat")
def ailovanta_chat(body: NativeChatRequest) -> dict:
    convo = conversations.get_or_create(body.conversation_id, body.user_id, body.title)
    conversations.add_message(convo["id"], "user", body.prompt, source="user", model_id=body.model_id)
    recent_messages = conversations.list_messages(convo["id"], limit=24)
    context_messages = build_chat_context(recent_messages, body.prompt, max_messages=12)

    owned_required = require_owned_chat()
    owned_error = None
    owned_error_readiness = None
    if owned_required or prefer_owned_chat():
        from api.owned_model_runtime import OwnedModelRequest, OwnedModelRuntime, OwnedModelUnavailable

        owned_model_id, owned_version = owned_model_target(body.model_id, body.version)
        try:
            result = OwnedModelRuntime(runtime_registry).generate(
                OwnedModelRequest(
                    prompt=body.prompt,
                    model_id=owned_model_id,
                    version=owned_version,
                    user_id=body.user_id,
                    conversation_id=convo["id"],
                )
            )
        except OwnedModelUnavailable as exc:
            owned_error = str(exc)
            owned_error_readiness = getattr(exc, "readiness", {}) or None
            if owned_required:
                answer = "Ailovanta owned model runtime is not ready: " + owned_error
                assistant_message = conversations.add_message(convo["id"], "assistant", answer, source="owned-runtime-unavailable", model_id=owned_model_id)
                return {
                    "conversation_id": convo["id"],
                    "answer": answer,
                    "source": "owned-runtime-unavailable",
                    "runtime_route": {"assigned": False, "reason": owned_error},
                    "assistant_message": assistant_message,
                    "context_messages_used": len(context_messages),
                    "owned_model_ready": False,
                    "self_trained_ready": False,
                    "model_readiness": owned_error_readiness,
                    "model_id": owned_model_id,
                    "version": owned_version,
                    "fallback_allowed": False,
                }
        else:
            worker_validation = validate_worker_result(
                result.worker_result,
                artifact_manifest=artifact_manifest_from_worker_result(result.worker_result),
                store=worker_validation_store(),
                reputation=worker_reputation_store(),
                apply_reputation=True,
            )
            assistant_message = conversations.add_message(convo["id"], "assistant", result.answer, source=result.source, model_id=result.model_id)
            usage_store.record(
                body.user_id,
                "ailovanta.chat.owned",
                1,
                result.source,
                {
                    "conversation_id": convo["id"],
                    "model_id": result.model_id,
                    "version": result.version,
                    "context_messages": len(context_messages),
                    "worker_validation_receipt_id": worker_validation["receipt_id"],
                    "worker_validation_passed": worker_validation["passed"],
                    "owned_selection": "preferred" if not owned_required else "required",
                },
            )
            owned_model_ready = bool(result.model_readiness.get("owned_model_ready"))
            return {
                "conversation_id": convo["id"],
                "answer": result.answer,
                "source": result.source,
                "runtime_route": result.runtime_route,
                "worker_validation": worker_validation,
                "assistant_message": assistant_message,
                "context_messages_used": len(context_messages),
                "owned_model_ready": owned_model_ready,
                "self_trained_ready": bool(result.model_readiness.get("self_trained_ready")),
                "model_readiness": result.model_readiness,
                "model_id": result.model_id,
                "version": result.version,
            }

    route = {"assigned": False, "reason": "runtime routing not requested"}
    if body.use_runtime_router:
        route = runtime_registry.route(RuntimeRequest(request_id=f"chat-{convo['id']}", model_id=body.model_id, version=body.version, region_hint="auto"))
    answer, source = answer_with_ollama(body.prompt, context_messages)
    assistant_message = conversations.add_message(convo["id"], "assistant", answer, source=source, model_id=body.model_id)
    usage_store.record(body.user_id, "ailovanta.chat", 1, source, {"conversation_id": convo["id"], "model_id": body.model_id, "context_messages": len(context_messages), "owned_runtime_error": owned_error})
    return {
        "conversation_id": convo["id"],
        "answer": answer,
        "source": source,
        "runtime_route": route,
        "assistant_message": assistant_message,
        "context_messages_used": len(context_messages),
        "owned_model_ready": False,
        "self_trained_ready": False,
        "model_readiness": owned_error_readiness,
        "owned_runtime_error": owned_error,
        "fallback_allowed": True,
    }


@app.get("/ailovanta/v1/conversations")
def list_conversations(user_id: str = "local", limit: int = 50) -> dict:
    return {"conversations": conversations.list_conversations(user_id=user_id, limit=limit)}


@app.post("/ailovanta/v1/conversations")
def create_conversation(user_id: str = "local", title: str = "New chat") -> dict:
    return conversations.create_conversation(user_id=user_id, title=title)


@app.get("/ailovanta/v1/conversations/{conversation_id}/messages")
def list_conversation_messages(conversation_id: str, limit: int = 100) -> dict:
    convo = conversations.get_conversation(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="conversation not found")
    return {"conversation": convo, "messages": conversations.list_messages(conversation_id, limit=limit)}


@app.delete("/ailovanta/v1/conversations/{conversation_id}")
def delete_conversation(conversation_id: str) -> dict:
    deleted = conversations.delete_conversation(conversation_id)
    return {"ok": bool(deleted), "deleted": deleted}


@app.post("/usage/events")
def record_usage_event(body: UsageEventRequest) -> dict:
    return {"ok": True, "event": usage_store.record(body.user_id, body.event_type, body.quantity, body.source, body.metadata)}


@app.get("/usage/events")
def list_usage_events(user_id: str | None = None, limit: int = 100) -> dict:
    return {"events": usage_store.list_events(user_id=user_id, limit=limit)}


@app.get("/usage/summary")
def usage_summary(user_id: str = "local") -> dict:
    return usage_store.summary(user_id)
