from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Open GPU Privacy AI API", version="0.4.0")

nodes: dict[str, dict] = {}
jobs: list[dict] = [
    {"id": "job-rag-001", "type": "rag_index", "payload": {"tokens": 1200}},
    {"id": "job-eval-001", "type": "evaluation", "payload": {"samples": 12}},
    {"id": "job-lora-001", "type": "lora_micro", "payload": {"steps": 20}},
]
results: list[dict] = []


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def root() -> dict:
    return {
        "name": "Open GPU Privacy AI",
        "version": "0.4.0",
        "status": "local runtime skeleton",
    }


@app.post("/nodes/register")
def register_node(body: NodeRegister) -> dict:
    node_id = "node_" + uuid4().hex[:12]
    score = body.cpu_threads * 8 + int(body.memory_gb * 10) + (60 if body.has_gpu else 10)
    nodes[node_id] = {
        **body.model_dump(),
        "node_id": node_id,
        "score": score,
        "trust": 30,
        "status": "online",
        "created_at": utc_now(),
        "last_seen": utc_now(),
    }
    return nodes[node_id]


@app.post("/nodes/heartbeat")
def heartbeat(body: Heartbeat) -> dict:
    node = nodes.get(body.node_id)
    if not node:
        return {"ok": False, "error": "node not found"}
    node["status"] = body.status
    node["last_seen"] = utc_now()
    return {"ok": True, "node": node}


@app.get("/jobs/next")
def next_job(node_id: str) -> dict:
    node = nodes.get(node_id)
    if not node:
        return {"ok": False, "error": "node not found"}
    if not jobs:
        return {"ok": True, "job": None}
    job = jobs.pop(0)
    job["assigned_to"] = node_id
    job["assigned_at"] = utc_now()
    return {"ok": True, "job": job}


@app.post("/jobs/result")
def submit_result(body: JobResult) -> dict:
    item = body.model_dump() | {"submitted_at": utc_now()}
    results.append(item)
    node = nodes.get(body.node_id)
    if node and body.status == "ok":
        node["trust"] = min(100, node.get("trust", 30) + 1)
    return {"ok": True, "accepted": item}


@app.post("/ai/chat")
def ai_chat(body: ChatRequest) -> dict:
    return {
        "mode": body.mode,
        "reply": (
            "This is the v0.4 local API skeleton. "
            "Next step: connect this endpoint to Ollama, local memory, and the scheduler."
        ),
    }


@app.get("/network/status")
def network_status() -> dict:
    return {
        "nodes": len(nodes),
        "queued_jobs": len(jobs),
        "submitted_results": len(results),
    }
