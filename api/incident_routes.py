from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.incident_response import IncidentResponse


router = APIRouter(prefix="/ops/incidents", tags=["incidents"])
controller = IncidentResponse()


class IncidentIn(BaseModel):
    route_key: str = "owned-chat/default"
    verify_bytes: bool = False
    verify_distribution: bool = False
    verify_chain: bool = False
    dry_run: bool = True


@router.post("/plan")
def plan_incident(body: IncidentIn) -> dict:
    return controller.plan(route_key=body.route_key, verify_bytes=body.verify_bytes, verify_distribution=body.verify_distribution, verify_chain=body.verify_chain)


@router.post("/execute")
def execute_incident(body: IncidentIn) -> dict:
    return controller.execute(route_key=body.route_key, verify_bytes=body.verify_bytes, verify_distribution=body.verify_distribution, verify_chain=body.verify_chain, dry_run=body.dry_run)


@router.get("/logs")
def list_incidents() -> dict:
    return {"items": controller.list_logs()}
