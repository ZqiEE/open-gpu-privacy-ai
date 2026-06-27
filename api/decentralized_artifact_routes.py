from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.artifact_store import get_artifact_store
from api.catalog import Catalog


router = APIRouter()
catalog = Catalog()


class StoreFileIn(BaseModel):
    local_path: str
    artifact_id: str
    metadata: dict = Field(default_factory=dict)


class StoreCatalogIn(BaseModel):
    local_path: str
    artifact_id: str
    name: str
    version: str
    source_job_id: str = "manual"
    kind: str = "adapter"
    metrics: dict = Field(default_factory=dict)
    receipt: dict | None = None
    status: str = "candidate"


@router.post("/artifacts/store")
def store_artifact(body: StoreFileIn) -> dict:
    stored = get_artifact_store().put_file(body.local_path, body.artifact_id, body.metadata)
    return {"artifact": stored.to_dict()}


@router.post("/artifacts/store-catalog")
def store_artifact_catalog(body: StoreCatalogIn) -> dict:
    stored = get_artifact_store().put_file(body.local_path, body.artifact_id, {"name": body.name, "version": body.version, **body.metrics})
    artifact = stored.to_dict()
    item = catalog.add({
        "name": body.name,
        "version": body.version,
        "source_job_id": body.source_job_id,
        "location": artifact["artifact_uri"],
        "artifact_uri": artifact["artifact_uri"],
        "artifact_hash": artifact["artifact_hash"],
        "kind": body.kind,
        "digest": artifact["artifact_hash"],
        "metrics": body.metrics,
        "proof": body.receipt,
        "status": body.status,
        "notes": f"stored via {artifact['store']}",
    })
    return {"artifact": artifact, "item": item}
