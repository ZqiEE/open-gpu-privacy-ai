from __future__ import annotations

from fastapi import APIRouter

from api.prod_ready_plus import check_production_ready_plus


router = APIRouter()


@router.get("/ops/readiness/plus")
def prod_ready_plus(route_key: str = "owned-chat/default", verify_bytes: bool = False, verify_distribution: bool = False, verify_chain: bool = False, result_path: str | None = None) -> dict:
    return check_production_ready_plus(result_path=result_path, route_key=route_key, verify_bytes=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
