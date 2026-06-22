from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.memory_store import MemoryStore
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable
from api.storage import SchedulerStore

app = FastAPI(title="Open GPU Privacy AI API", version="0.7.0")

store = SchedulerStore()
memories = MemoryStore()
ollama = OllamaAdapter()


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


class ChatRequest(BaseModel):
    prompt: str
    mode: Literal["standard", "open", "creative", "private_companion"] = "open"
    user_id: str = "local"
    remember: bool = False


class MemoryRequest(BaseModel):
    memory: str
    user_id: str = "local"


@app.get("/")
def root() -> dict:
    return {
        "name": "Open GPU Privacy AI",
        "version": "0.7.0",
        "status": "scheduler persistence skeleton",
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
    return {"ok": True, "accepted": accepted}


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
            "The scheduler now persists nodes, jobs, and results in SQLite."
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
