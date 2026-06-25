from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.g2 import run_gate

router = APIRouter(prefix="/gg", tags=["gg"])


class Body(BaseModel):
    result_path: str
    core_path: str = "../ailovanta-core"
    work_dir: str = "runtime_data/g2"


@router.post("/run")
def run(body: Body) -> dict[str, Any]:
    return run_gate(result_path=body.result_path, core_path=body.core_path, work_dir=body.work_dir)
