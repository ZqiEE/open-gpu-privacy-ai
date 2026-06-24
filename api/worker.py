from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Ailovanta Worker", version="1.0.1")


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-worker", "mode": "backend-required"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    try:
        from api.model_backend_client import ModelBackendClient

        answer = ModelBackendClient().chat(prompt=body.prompt)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="model backend unavailable: " + str(exc)) from exc

    return {
        "answer": answer,
        "source": "ailovanta-worker-v1",
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
    }
