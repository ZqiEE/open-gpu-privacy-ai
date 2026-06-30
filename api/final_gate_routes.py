from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.release_gate import release_gate


router = APIRouter(prefix="/ops/release", tags=["release"])


class ReleaseGateIn(BaseModel):
    core_path: str = "../ailovanta-core"
    result_path: str | None = None
    route_key: str = "owned-chat/default"
    run_tests: bool = False
    verify_bytes: bool = False
    verify_distribution: bool = False
    verify_chain: bool = False


@router.post("/gate")
def run_release_gate(body: ReleaseGateIn) -> dict:
    return release_gate(core_path=body.core_path, result_path=body.result_path, route_key=body.route_key, run_tests=body.run_tests, verify_bytes=body.verify_bytes, verify_distribution=body.verify_distribution, verify_chain=body.verify_chain)
