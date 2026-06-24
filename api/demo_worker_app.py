from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Ailovanta Demo Worker", version="0.1.0")


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    policy_mode: str = "open_research"
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-demo-worker"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    text = "Ailovanta worker response from " + body.runtime_id + " using " + body.model_id + ":" + body.version
    return {
        "answer": text + ". Prompt received: " + body.prompt,
        "source": "ailovanta-demo-worker",
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
        "policy_mode": body.policy_mode,
    }
