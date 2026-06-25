from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.autonomous_loop import AutonomousLoop

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
    max_steps: int = 100
    model_id: str = "ailovanta-owned"
    target_version: str = "candidate"


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
