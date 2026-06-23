from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api.dashboard import DashboardService
from api.health import get_health
from api.memory_store import MemoryStore
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable
from api.reputation import ReputationService
from api.runtime_router import ModelManifest, RuntimeNodeProfile, RuntimeRequest
from api.runtime_store import RuntimeStore
from api.storage import SchedulerStore
from api.training import TrainingKind, TrainingPlanner
from api.usage_store import UsageStore
from api.verification import VerificationEngine

APP_VERSION = "1.6.0"
TRAINING_JOB_TYPES = {"rag_import", "lora_micro", "evaluation_batch", "private_memory_tune"}
BASE_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(title="Ailovanta API", version=APP_VERSION)

store = SchedulerStore()
usage_store = UsageStore()
dashboard = DashboardService(store)
reputation = ReputationService(store)
memories = MemoryStore()
ollama = OllamaAdapter()
verifier = VerificationEngine()
training = TrainingPlanner()
runtime_registry = RuntimeStore()


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
    kind: TrainingKind
    name: str
    dataset_uri: str
    base_model: str = "qwen2.5:3b"
    max_steps: int = Field(default=100, ge=1, le=10000)
    notes: str = ""


class ModelVersionRequest(BaseModel):
    name: str
    base_model: str
    source_job_id: str
    notes: str = ""


class ChatRequest(BaseModel):
    prompt: str
    mode: Literal["standard", "open", "creative", "private_work"] = "open"
    user_id: str = "local"
    remember: bool = False


class MemoryRequest(BaseModel):
    memory: str
    user_id: str = "local"


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


@app.get("/")
def root() -> dict:
    return {
        "name": "Ailovanta",
        "version": APP_VERSION,
        "tagline": "AI powered by the world's distributed compute.",
        "app": "/app",
        "dashboard": "/dashboard",
        "docs": "/docs",
        "scheduler": store.status(),
        "runtime": runtime_registry.status(),
    }


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


@app.get("/health")
def health() -> dict:
    return get_health(APP_VERSION)


@app.get("/ready")
def ready() -> dict:
    status = store.status()
    return {"ok": True, "scheduler_store": status["store"], "path": status["path"]}


@app.get("/network/status")
def network_status() -> dict:
    return store.status()


@app.get("/verification/status")
def verification_status() -> dict:
    status = store.status()
    return {
        "verifications": status["verifications"],
        "passed_verifications": status["passed_verifications"],
        "pass_rate": round(status["passed_verifications"] / status["verifications"], 3) if status["verifications"] else 0.0,
    }


@app.post("/jobs/retry-failed")
def retry_failed_jobs(max_attempts: int = 3) -> dict:
    return store.retry_failed_jobs(max_attempts=max_attempts)


@app.post("/jobs/requeue-stale")
def requeue_stale_jobs(older_than_minutes: int = 30) -> dict:
    return store.requeue_stale_assigned(older_than_minutes=older_than_minutes)


@app.post("/nodes/register")
def register_node(body: NodeRegister) -> dict:
    return store.register_node(body.model_dump())


@app.get("/nodes")
def list_nodes(limit: int = 50) -> dict:
    return {"nodes": store.list_nodes(limit=limit)}


@app.post("/nodes/heartbeat")
def heartbeat(body: Heartbeat) -> dict:
    node = store.update_heartbeat(body.node_id, body.status)
    if not node:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@app.get("/jobs/next")
def next_job(node_id: str) -> dict:
    return {"job": store.next_job(node_id)}


@app.get("/jobs")
def list_jobs(status: str | None = None, limit: int = 50) -> dict:
    return {"jobs": store.list_jobs(status=status, limit=limit)}


@app.post("/jobs/result")
def submit_result(body: JobResult) -> dict:
    result = store.submit_result(body.model_dump())
    scored = verifier.score_result(body.job_id, body.node_id, body.status, body.output_summary)
    verification = store.record_verification(result, scored.score, scored.passed, scored.reason)
    return {"ok": True, "result": result, "verification": verification}


@app.post("/runtime/models/register")
def register_runtime_model(body: RuntimeModelRegister) -> dict:
    manifest = ModelManifest(**body.model_dump())
    return {"ok": True, "model": runtime_registry.register_model(manifest)}


@app.get("/runtime/models")
def list_runtime_models() -> dict:
    return {"models": runtime_registry.list_models()}


@app.post("/runtime/nodes/register")
def register_runtime_node(body: RuntimeNodeRegister) -> dict:
    profile = RuntimeNodeProfile(**body.model_dump())
    return {"ok": True, "runtime": runtime_registry.register_runtime(profile)}


@app.get("/runtime/nodes")
def list_runtime_nodes() -> dict:
    return {"runtimes": runtime_registry.list_runtimes()}


@app.get("/runtime/status")
def runtime_status() -> dict:
    return runtime_registry.status()


@app.get("/runtime/assignments")
def list_runtime_assignments(limit: int = 50) -> dict:
    return {"assignments": runtime_registry.list_assignments(limit=limit)}


@app.post("/runtime/route")
def route_runtime_request(body: RuntimeRouteRequest) -> dict:
    request = RuntimeRequest(**body.model_dump())
    return runtime_registry.route(request)


@app.post("/training/jobs")
def create_training_job(body: TrainingJobRequest) -> dict:
    job = training.build_job(body.kind, body.name, body.dataset_uri, body.base_model, body.max_steps, body.notes)
    saved = store.enqueue_job(job["job_id"], job["job_type"], job["payload"])
    return {"ok": True, "job": saved}


@app.get("/training/jobs")
def list_training_jobs(limit: int = 50) -> dict:
    jobs = [job for job in store.list_jobs(limit=limit) if job["type"] in TRAINING_JOB_TYPES]
    return {"jobs": jobs}


@app.post("/models/versions")
def create_model_version(body: ModelVersionRequest) -> dict:
    record = training.build_model_version(body.name, body.base_model, body.source_job_id, body.notes)
    saved = store.register_model_version(record)
    return {"ok": True, "model": saved}


@app.get("/models/versions")
def list_model_versions(limit: int = 50) -> dict:
    return {"models": store.list_model_versions(limit=limit)}


@app.get("/dashboard/summary")
def dashboard_summary() -> dict:
    return dashboard.summary()


@app.get("/dashboard/jobs")
def dashboard_jobs(limit: int = 20) -> dict:
    return dashboard.recent_jobs(limit=limit)


@app.get("/dashboard/models")
def dashboard_models(limit: int = 20) -> dict:
    return dashboard.model_versions(limit=limit)


@app.post("/ai/chat")
def chat(body: ChatRequest) -> dict:
    memory = memories.list(body.user_id)
    try:
        answer = ollama.chat(body.prompt, body.mode, memory)
        source = "ollama"
    except OllamaUnavailable:
        answer = "Ailovanta local fallback: connect a local model runtime to enable real AI responses."
        source = "fallback"
    usage_store.record(body.user_id, "chat", 1, source, {"mode": body.mode})
    if body.remember:
        memories.add(body.prompt, body.user_id)
    return {"answer": answer, "source": source}


@app.get("/usage/summary")
def usage_summary(user_id: str = "local") -> dict:
    return usage_store.summary(user_id=user_id)


@app.post("/memory")
def add_memory(body: MemoryRequest) -> dict:
    return {"memories": memories.add(body.memory, body.user_id)}


@app.get("/memory")
def list_memory(user_id: str = "local") -> dict:
    return {"memories": memories.list(user_id)}


@app.delete("/memory")
def wipe_memory(user_id: str = "local") -> dict:
    memories.wipe(user_id)
    return {"ok": True}
