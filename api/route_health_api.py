from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from api.route_health import RouteHealth

router = APIRouter(prefix="/route-health", tags=["route-health"])


class RouteHealthBody(BaseModel):
    route_key: str = "owned-chat/default"
    disable_if_bad: bool = False
    verify_artifact: bool = False
    verify_distribution: bool = False
    verify_chain: bool = False


@router.post("/check")
def check_route_health(body: RouteHealthBody) -> dict[str, Any]:
    checker = RouteHealth()
    if body.disable_if_bad:
        return checker.disable_if_bad(body.route_key, verify_artifact=body.verify_artifact, verify_distribution=body.verify_distribution, verify_chain=body.verify_chain)
    return checker.check(body.route_key, verify_artifact=body.verify_artifact, verify_distribution=body.verify_distribution, verify_chain=body.verify_chain)


@router.get("/{route_key:path}")
def get_route_health(route_key: str, verify_artifact: bool = False, verify_distribution: bool = False, verify_chain: bool = False) -> dict[str, Any]:
    return RouteHealth().check(route_key, verify_artifact=verify_artifact, verify_distribution=verify_distribution, verify_chain=verify_chain)
