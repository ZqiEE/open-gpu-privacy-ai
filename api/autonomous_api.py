from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.autonomous_loop import AutonomousLoop
from api.autonomous_code_training_loop import AutonomousCodeTrainingLoop

router = APIRouter(prefix="/autonomous", tags=["autonomous"])


class RunRequest(BaseModel):
    core_path: str | None = None
    root: str = "runtime_data/autonomous_loop"
    baseline_model: str = "ailovanta-owned:baseline"
    baseline_score: float = 0.45
    allow_shadow_import: bool = False
    execute_checkpoints: bool = False
    checkpoint_output_root: str | None = None
    training_command: str | None = None
    model_backend: str | None = None
    base_model: str | None = None
    backend_output_dir: str | None = None
    backend_device: str | None = None
    backend_max_steps: int | None = None
    backend_lr: float | None = None
    max_steps: int = 100
    model_id: str = "ailovanta-owned"
    target_version: str = "candidate"


class CodeRunRequest(BaseModel):
    core_path: str | None = None
    root: str = "runtime_data/autonomous_code_loop"
    sources_path: str = "runtime_data/github_code_sources.json"
    discover: bool = False
    fetch: bool = True
    corpus_mode: str = "instructions"
    max_sources: int | None = None
    max_tasks: int = 50
    run_foundation: bool = True
    execute_checkpoints: bool = True
    model_id: str = "ailovanta-code"
    target_version: str = "candidate"
    max_steps: int = 100
    training_command: str | None = None


@router.post("/run")
def run_once(body: RunRequest) -> dict[str, Any]:
    try:
        loop = AutonomousLoop(core_path=body.core_path, root=body.root)
        return loop.run_once(
            baseline_model=body.baseline_model,
            baseline_score=body.baseline_score,
            allow_shadow_import=body.allow_shadow_import,
            execute_checkpoints=body.execute_checkpoints,
            checkpoint_output_root=body.checkpoint_output_root,
            training_command=body.training_command,
            model_backend=body.model_backend,
            base_model=body.base_model,
            backend_output_dir=body.backend_output_dir,
            backend_device=body.backend_device,
            backend_max_steps=body.backend_max_steps,
            backend_lr=body.backend_lr,
            max_steps=body.max_steps,
            model_id=body.model_id,
            target_version=body.target_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/latest")
def latest(root: str = "runtime_data/autonomous_loop") -> dict:
    return {"run": AutonomousLoop(root=root).latest_run()}


@router.get("/runs")
def list_runs(root: str = "runtime_data/autonomous_loop") -> dict:
    return {"items": AutonomousLoop(root=root).list_runs()}


@router.post("/code/run")
def run_code_once(body: CodeRunRequest) -> dict[str, Any]:
    try:
        return AutonomousCodeTrainingLoop(core_path=body.core_path, root=body.root).run_once(
            sources_path=body.sources_path,
            discover=body.discover,
            fetch=body.fetch,
            corpus_mode=body.corpus_mode,
            max_sources=body.max_sources,
            max_tasks=body.max_tasks,
            run_foundation=body.run_foundation,
            execute_checkpoints=body.execute_checkpoints,
            model_id=body.model_id,
            target_version=body.target_version,
            max_steps=body.max_steps,
            training_command=body.training_command,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/code/latest")
def latest_code(root: str = "runtime_data/autonomous_code_loop") -> dict:
    return {"run": AutonomousCodeTrainingLoop(root=root).latest_run()}


@router.get("/code/runs")
def list_code_runs(root: str = "runtime_data/autonomous_code_loop") -> dict:
    return {"items": AutonomousCodeTrainingLoop(root=root).list_runs()}
