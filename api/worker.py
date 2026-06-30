from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.artifact_binding import ArtifactBindingStore
from api.bound_runtime import ArtifactBoundRuntime, BoundRuntimeUnavailable
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable

app = FastAPI(title="Ailovanta Worker", version="1.0.5")


class InferRequest(BaseModel):
    prompt: str
    model_id: str
    version: str
    runtime_id: str
    node_id: str
    model_manifest_hash: str
    policy_mode: str = "open_research"


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "ailovanta-worker",
        "mode": "artifact-bound-runtime",
        "bootstrap_fallback": allow_bootstrap_fallback(),
    }


def binding_store() -> ArtifactBindingStore:
    return ArtifactBindingStore(os.getenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", "runtime_data/artifact_bindings.sqlite3"))


def allow_bootstrap_fallback() -> bool:
    return os.getenv("AILOVANTA_WORKER_ALLOW_BOOTSTRAP_FALLBACK", "").lower() in {"1", "true", "yes", "on"}


def resolve_binding(model_id: str, version: str) -> dict | None:
    try:
        return binding_store().latest_for_model_statuses(f"{model_id}:{version}", ("active",))
    except Exception:
        return None


@app.post("/v1/owned/infer")
def infer(body: InferRequest) -> dict:
    binding = resolve_binding(body.model_id, body.version)
    if binding:
        expected_hash = binding.get("runtime_manifest_hash")
        if expected_hash and expected_hash != body.model_manifest_hash:
            raise HTTPException(
                status_code=409,
                detail={
                    "reason": "model_manifest_hash_mismatch",
                    "expected": expected_hash,
                    "actual": body.model_manifest_hash,
                },
            )
        try:
            bound = ArtifactBoundRuntime(binding_store()).chat(body.prompt, body.model_id, body.version)
        except BoundRuntimeUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail={"reason": "artifact_bound_runtime_unavailable", "message": str(exc)},
            ) from exc
        answer = bound["answer"]
        source = bound["source"]
        binding = bound.get("binding") or binding
    elif allow_bootstrap_fallback():
        try:
            answer = OllamaAdapter().chat(body.prompt, body.policy_mode, [])
            source = "ailovanta-worker-bootstrap-fallback"
        except OllamaUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail={"reason": "bootstrap_runtime_unavailable", "message": str(exc)},
            ) from exc
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "reason": "missing_artifact_binding",
                "model_key": f"{body.model_id}:{body.version}",
            },
        )

    return {
        "answer": answer,
        "source": source,
        "model_id": body.model_id,
        "version": body.version,
        "runtime_id": body.runtime_id,
        "node_id": body.node_id,
        "model_manifest_hash": body.model_manifest_hash,
        "policy_mode": body.policy_mode,
        "artifact_binding": binding,
        "validation_provenance": {
            "schema_version": "ailovanta.worker_result_provenance.v1",
            "binding_id": binding.get("binding_id") if binding else None,
            "runtime_manifest_hash": binding.get("runtime_manifest_hash") if binding else None,
            "artifact_hash": binding.get("artifact_hash") if binding else None,
            "backend_kind": binding.get("backend_kind") if binding else None,
            "backend_ref": binding.get("backend_ref") if binding else None,
        },
    }
