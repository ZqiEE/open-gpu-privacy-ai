from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.artifact_versions import ArtifactVersions


router = APIRouter()
versions = ArtifactVersions()


class ArtifactVersionIn(BaseModel):
    name: str
    version: str
    location: str
    catalog_item_id: str | None = None
    previous_artifact_id: str | None = None
    metadata: dict = {}


class RollbackIn(BaseModel):
    artifact_id: str


@router.post("/ops/artifacts/versions")
def create_artifact_version(body: ArtifactVersionIn) -> dict:
    return versions.create(body.name, body.version, body.location, body.catalog_item_id, body.previous_artifact_id, body.metadata)


@router.get("/ops/artifacts/versions")
def list_artifact_versions(name: str | None = None, limit: int = 100) -> dict:
    return {"versions": versions.list(name=name, limit=limit)}


@router.get("/ops/artifacts/active/{name}")
def active_artifact(name: str) -> dict:
    return {"active": versions.active(name)}


@router.post("/ops/artifacts/rollback/{name}")
def rollback_artifact(name: str, body: RollbackIn) -> dict:
    return versions.rollback(name, body.artifact_id)
