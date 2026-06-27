from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.queue_control import QueueControl


router = APIRouter()
queue = QueueControl()


class QueueLimitsIn(BaseModel):
    max_queued: int = Field(default=1000, ge=1)
    max_assigned: int = Field(default=100, ge=1)
    max_per_node_assigned: int = Field(default=3, ge=1)


@router.get("/ops/queue")
def queue_snapshot() -> dict:
    return queue.snapshot()


@router.post("/ops/queue/limits")
def update_queue_limits(body: QueueLimitsIn) -> dict:
    return queue.update(body.max_queued, body.max_assigned, body.max_per_node_assigned)


@router.get("/ops/queue/can-enqueue")
def can_enqueue() -> dict:
    return queue.can_enqueue()


@router.get("/ops/queue/can-assign/{node_id}")
def can_assign(node_id: str) -> dict:
    return queue.can_assign(node_id)
