from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.receipt_apply import apply_result

router = APIRouter(prefix="/apply", tags=["apply"])


class ApplyRequest(BaseModel):
    result_path: str
    runtime_id: str = "rt-owned-1"
    node_id: str = "node-owned-1"
    verify_artifact: bool | None = None
    verify_distribution: bool | None = None
    verify_chain: bool | None = None


@router.post("/result")
def apply_foundation_result(body: ApplyRequest) -> dict[str, Any]:
    return apply_result(body.result_path, runtime_id=body.runtime_id, node_id=body.node_id, verify_artifact=body.verify_artifact, verify_distribution=body.verify_distribution, verify_chain=body.verify_chain)
