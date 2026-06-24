from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.ollama_adapter import OllamaAdapter, OllamaUnavailable

app = FastAPI(title="Ailovanta Worker", version="1.0.2")


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "ailovanta-worker", "mode": "local-model-runtime"}


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    try:
        from api.model_backend_client import ModelBackendClient

        answer = ModelBackendClient().chat(prompt=body.prompt)
        source = "ailovanta-worker-backend"
    except Exception:
        try:
            answer = OllamaAdapter().chat(body.prompt, "open_research", [])
            source = "ailovanta-worker-local-runtime"
        except OllamaUnavailable as exc:
            raise HTTPException(status_code=503, detail="model runtime unavailable: " + str(exc)) from exc

    return {
        "answer": answer,
        "source": source,
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
    }
