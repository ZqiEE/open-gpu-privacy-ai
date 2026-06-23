from __future__ import annotations

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.dashboard import DashboardService
from api.health import get_health
from api.memory_store import MemoryStore
from api.ollama_adapter import OllamaAdapter, OllamaUnavailable
from api.reputation import ReputationService
from api.storage import SchedulerStore
from api.training import TrainingKind, TrainingPlanner
from api.usage_store import UsageStore
from api.verification import VerificationEngine

APP_VERSION = "1.5.0"

app = FastAPI(title="Ailovanta API", version=APP_VERSION)

store = SchedulerStore()
usage_store = UsageStore()
dashboard = DashboardService(store)
reputation = ReputationService(store)
memories = MemoryStore()
ollama = OllamaAdapter()
verifier = VerificationEngine()
training = TrainingPlanner()


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
