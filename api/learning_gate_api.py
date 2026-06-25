from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.learning_gate import run_guarded_learning_pipeline

router = APIRouter(prefix="/learning/gate", tags=["learning-gate"])


class GuardedLearningRequest(BaseModel):
    core_path: str | None = None
    work_dir: str = "runtime_data/guarded_learning_pipeline"
    baseline_model: str = "ailovanta-owned:baseline"
    baseline_score: float = 0.45
    allow_shadow_import: bool = False
    execute_checkpoints: bool = False
    checkpoint_output_root: str | None = None
    training_command: str | None = None
    model_id: str = "ailovanta-owned"
    target_version: str = "candidate"
    node_id: str = "learning_node_1"
    gpu_memory_gb: float = 24.0
    max_steps: int = 100


@router.post("/run")
def run_guarded_learning(body: GuardedLearningRequest) -> dict[str, Any]:
    try:
        return run_guarded_learning_pipeline(
            core_path=body.core_path,
            work_dir=body.work_dir,
            baseline_model=body.baseline_model,
            baseline_score=body.baseline_score,
            allow_shadow_import=body.allow_shadow_import,
            execute_checkpoints=body.execute_checkpoints,
            checkpoint_output_root=body.checkpoint_output_root,
            training_command=body.training_command,
            model_id=body.model_id,
            target_version=body.target_version,
            node_id=body.node_id,
            gpu_memory_gb=body.gpu_memory_gb,
            max_steps=body.max_steps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
