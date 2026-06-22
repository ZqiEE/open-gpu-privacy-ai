from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.memory_store import MemoryStore
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable
from api.storage import SchedulerStore
from api.training import TrainingKind, TrainingPlanner
from api.verification import VerificationEngine

app = FastAPI(title="Open GPU Privacy AI API", version="0.9.1")

store = SchedulerStore()
memories = MemoryStore()
ollama = OllamaAdapter()
verifier = VerificationEngine()
training = TrainingPlanner()


class NodeRegister(BaseModel):
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


@app.get("/")
def root() -> dict:
    return {
        "name": "Open GPU Privacy AI",
        "version": "0.9.1",
        "status": "focused private AI compute network",
        "scheduler": store.status(),
        "ollama_base_url": ollama.config.base_url,
        "ollama_model": ollama.config.model,
    }


@app.post("/nodes/register")
def register_node(body: NodeRegister) -> dict:
    return store.register_node(body.model_dump())


@app.post("/nodes/heartbeat")
def heartbeat(body: Heartbeat) -> dict:
    node = store.update_heartbeat(body.node_id, body.status)
    if not node:
        return {"ok": False, "error": "node not found"}
    return {"ok": True, "node": node}


@app.get("/jobs")
def list_jobs(status: str | None = None, limit: int = 50) -> dict:
    return {"jobs": store.list_jobs(status=status, limit=limit)}


@app.get("/jobs/next")
def next_job(node_id: str) -> dict:
    node = store.get_node(node_id)
    if not node:
        return {"ok": False, "error": "node not found"}
    return {"ok": True, "job": store.next_job(node_id)}


@app.post("/jobs/result")
def submit_result(body: JobResult) -> dict:
    node = store.get_node(body.node_id)
    if not node:
        return {"ok": False, "error": "node not found"}
    accepted = store.submit_result(body.model_dump())
    verification = verifier.score_result(body.job_id, body.node_id, body.status, body.output_summary)
    verified = store.record_verification(accepted, verification.score, verification.passed, verification.reason)
    return {"ok": True, "accepted": accepted, "verification": verified}


@app.post("/jobs/retry-failed")
def retry_failed(max_attempts: int = 3) -> dict:
    return {"ok": True, **store.retry_failed_jobs(max_attempts=max_attempts)}


@app.post("/jobs/requeue-stale")
def requeue_stale(older_than_minutes: int = 30) -> dict:
    return {"ok": True, **store.requeue_stale_assigned(older_than_minutes=older_than_minutes)}


@app.post("/training/jobs")
def create_training_job(body: TrainingJobRequest) -> dict:
    job = training.build_job(body.kind, body.name, body.dataset_uri, body.base_model, body.max_steps, body.notes)
    queued = store.enqueue_job(job["job_id"], job["job_type"], job["payload"])
    return {"ok": True, "job": queued}


@app.get("/training/jobs")
def list_training_jobs(limit: int = 50) -> dict:
    jobs = [job for job in store.list_jobs(limit=limit) if job["type"] in {"rag_import", "lora_micro", "evaluation_batch", "private_memory_tune"}]
    return {"jobs": jobs}


@app.post("/models/versions")
def create_model_version(body: ModelVersionRequest) -> dict:
    record = training.build_model_version(body.name, body.base_model, body.source_job_id, body.notes)
    return {"ok": True, "model": store.register_model_version(record)}


@app.get("/models/versions")
def list_model_versions(limit: int = 50) -> dict:
    return {"models": store.list_model_versions(limit=limit)}


@app.get("/verification/status")
def verification_status() -> dict:
    status = store.status()
    return {
        "verifications": status["verifications"],
        "passed_verifications": status["passed_verifications"],
        "failed_verifications": status["verifications"] - status["passed_verifications"],
    }


@app.post("/ai/chat")
def ai_chat(body: ChatRequest) -> dict:
    memory = memories.list(body.user_id)
    if body.remember:
        memories.add(f"User asked in {body.mode} mode: {body.prompt[:180]}", body.user_id)
        memory = memories.list(body.user_id)
    try:
        reply = ollama.chat(body.prompt, mode=body.mode, memory=memory)
        provider = "ollama"
    except OllamaUnavailable as exc:
        provider = "fallback"
        reply = (
            "Ollama is not available yet, so this is the fallback local runtime reply. "
            "Start Ollama and pull a model to enable real local AI. "
            "This project is focused on a private AI compute network, node scheduling, and training jobs."
        )
        error = str(exc)
    else:
        error = None
    return {"provider": provider, "mode": body.mode, "reply": reply, "error": error, "memory_items": len(memory)}


@app.get("/memory")
def list_memory(user_id: str = "local") -> dict:
    return {"user_id": user_id, "memory": memories.list(user_id)}


@app.post("/memory")
def add_memory(body: MemoryRequest) -> dict:
    return {"user_id": body.user_id, "memory": memories.add(body.memory, body.user_id)}


@app.delete("/memory")
def wipe_memory(user_id: str = "local") -> dict:
    memories.wipe(user_id)
    return {"ok": True, "user_id": user_id, "memory": []}


@app.get("/network/status")
def network_status() -> dict:
    return store.status()
