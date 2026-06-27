from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.event_log import EventLog
from api.runtime_store import RuntimeStore
from api.storage import SchedulerStore


router = APIRouter()
log = EventLog()
store = SchedulerStore()
runtime = RuntimeStore()


class EventIn(BaseModel):
    level: str = "info"
    source: str = "api"
    message: str
    metadata: dict = {}


@router.post("/ops/events")
def write_event(body: EventIn) -> dict:
    return log.write(body.level, body.source, body.message, body.metadata)


@router.get("/ops/events")
def list_events(level: str | None = None, limit: int = 100) -> dict:
    return {"events": log.list(level=level, limit=limit)}


@router.get("/ops/metrics")
def metrics() -> dict:
    scheduler = store.status()
    return {"scheduler": scheduler, "runtime": runtime.status(), "events": log.summary()}


@router.get("/ops/healthz")
def healthz() -> dict:
    scheduler = store.status()
    ok = scheduler["failed_jobs"] < max(10, scheduler["done_jobs"] + 10)
    return {"ok": ok, "scheduler": scheduler, "runtime": runtime.status()}
