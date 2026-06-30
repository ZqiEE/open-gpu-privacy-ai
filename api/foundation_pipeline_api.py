from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.foundation_pipeline import run_foundation_pipeline

router = APIRouter(prefix="/foundation/pipeline", tags=["foundation-pipeline"])


class FoundationPipelineRequest(BaseModel):
    job_id: str
    core_path: str | None = None
    work_dir: str = "runtime_data/foundation_pipeline"
    execute_checkpoints: bool = False
    checkpoint_output_root: str | None = None
    training_command: str | None = None


@router.post("/run")
def run_pipeline(body: FoundationPipelineRequest) -> dict:
    try:
        result = run_foundation_pipeline(
            body.job_id,
            core_path=body.core_path,
            work_dir=body.work_dir,
            execute_checkpoints=body.execute_checkpoints,
            checkpoint_output_root=body.checkpoint_output_root,
            training_command=body.training_command,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
