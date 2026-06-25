from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.autotruth_store import AutoTruthEventStore

router = APIRouter(prefix="/learning", tags=["learning"])
store = AutoTruthEventStore()


class EventIn(BaseModel):
    input: str
    output: str
    source: str = "public-runtime"
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    behavior: dict[str, Any] = Field(default_factory=dict)


class RunIn(BaseModel):
    payload: dict[str, Any]


class ExportIn(BaseModel):
    output_path: str = "runtime_data/autotruth_public/events_export.json"


@router.post("/events")
def add_event(body: EventIn) -> dict:
    try:
        return {"ok": True, "event": store.add_event(body.model_dump())}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/events")
def list_events(limit: int = 200) -> dict:
    return {"events": store.list_events(limit=limit)}


@router.post("/export")
def export_events(body: ExportIn) -> dict:
    return {"ok": True, "result": store.export_events(body.output_path)}


@router.post("/runs")
def import_run(body: RunIn) -> dict:
    return {"ok": True, "result": store.import_run(body.payload)}


@router.get("/runs/latest")
def latest_run() -> dict:
    return {"run": store.latest_run()}


@router.get("/packs/latest")
def latest_pack() -> dict:
    return {"pack": store.latest_pack()}
