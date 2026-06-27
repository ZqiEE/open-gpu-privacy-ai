from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.catalog import Catalog
from api.object_store import get_object, presign_get, put_object


router = APIRouter()
catalog = Catalog()


class PutObjectIn(BaseModel):
    local_path: str
    key: str
    bucket: str | None = None


class GetObjectIn(BaseModel):
    key: str
    output_path: str
    bucket: str | None = None


class PresignIn(BaseModel):
    key: str
    bucket: str | None = None
    expires: int = Field(default=3600, ge=60, le=604800)


class CatalogObjectIn(BaseModel):
    name: str
    version: str
    local_path: str
    key: str
    bucket: str | None = None
    source_job_id: str = "object_upload"
    kind: str = "artifact"
    score: float = 0.7


@router.post("/objects/put")
def object_put(body: PutObjectIn) -> dict:
    return put_object(body.local_path, body.key, body.bucket)


@router.post("/objects/get")
def object_get(body: GetObjectIn) -> dict:
    return get_object(body.key, body.output_path, body.bucket)


@router.post("/objects/presign")
def object_presign(body: PresignIn) -> dict:
    return presign_get(body.key, body.bucket, body.expires)


@router.post("/objects/put-catalog")
def object_put_catalog(body: CatalogObjectIn) -> dict:
    obj = put_object(body.local_path, body.key, body.bucket)
    item = catalog.add({"name": body.name, "version": body.version, "source_job_id": body.source_job_id, "location": obj["uri"], "kind": body.kind, "metrics": {"score": body.score}, "status": "candidate", "notes": "synced to object store"})
    return {"object": obj, "item": item}


@router.post("/objects/get-catalog")
def object_get_catalog(body: CatalogObjectIn) -> dict:
    obj = get_object(body.key, body.local_path, body.bucket)
    item = catalog.add({"name": body.name, "version": body.version, "source_job_id": body.source_job_id, "location": obj["output_path"], "kind": body.kind, "metrics": {"score": body.score}, "status": "candidate", "notes": "downloaded from object store"})
    return {"object": obj, "item": item}
