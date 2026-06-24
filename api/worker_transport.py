from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class WorkerInferenceUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerInferenceRequest:
    prompt: str
    model_id: str
    version: str
    policy_mode: str
    runtime_id: str
    node_id: str
    model_manifest_hash: str


@dataclass(frozen=True)
class WorkerInferenceResult:
    answer: str
    source: str
    worker_url: str
    runtime_id: str
    node_id: str
    raw: dict[str, Any]


class WorkerInferenceClient:
    def __init__(self, timeout_seconds: float | None = None) -> None:
        self.timeout_seconds = timeout_seconds or float(os.getenv("AILOVANTA_WORKER_TIMEOUT_SECONDS", "60"))

    def infer(self, request: WorkerInferenceRequest) -> WorkerInferenceResult:
        worker_url = self.worker_url(request.runtime_id)
        payload = {
            "prompt": request.prompt,
            "model_id": request.model_id,
            "version": request.version,
            "policy_mode": request.policy_mode,
            "runtime_id": request.runtime_id,
            "node_id": request.node_id,
            "model_manifest_hash": request.model_manifest_hash,
        }
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{worker_url}/v1/owned/infer", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise WorkerInferenceUnavailable(str(exc)) from exc

        answer = str(data.get("answer") or "").strip()
        if not answer:
            raise WorkerInferenceUnavailable("worker returned empty answer")
        return WorkerInferenceResult(
            answer=answer,
            source="ailovanta-worker",
            worker_url=worker_url,
            runtime_id=request.runtime_id,
            node_id=request.node_id,
            raw=data,
        )

    @staticmethod
    def worker_url(runtime_id: str) -> str:
        key = "AILOVANTA_WORKER_URL_" + runtime_id.upper().replace("-", "_")
        specific = os.getenv(key)
        if specific:
            return specific.rstrip("/")
        default = os.getenv("AILOVANTA_DEFAULT_WORKER_URL")
        if default:
            return default.rstrip("/")
        raise WorkerInferenceUnavailable(f"worker url not configured for runtime: {runtime_id}")
