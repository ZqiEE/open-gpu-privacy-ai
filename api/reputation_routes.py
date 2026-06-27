from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.admin_security import admin_token_header
from api.reputation_ops import ReputationOps


router = APIRouter(dependencies=[Depends(admin_token_header)])
rep = ReputationOps()


class ReputationEventIn(BaseModel):
    node_id: str
    event_type: str
    delta: float
    reason: str
    metadata: dict = {}


@router.post("/ops/reputation/events")
def add_reputation_event(body: ReputationEventIn) -> dict:
    return rep.add_event(body.node_id, body.event_type, body.delta, body.reason, body.metadata)


@router.get("/ops/reputation/events")
def list_reputation_events(node_id: str | None = None, limit: int = 100) -> dict:
    return {"events": rep.list_events(node_id=node_id, limit=limit)}


@router.get("/ops/reputation/{node_id}")
def reputation_scorecard(node_id: str) -> dict:
    return rep.scorecard(node_id)
