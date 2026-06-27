from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.object_store import get_object, presign_get, put_object


router = APIRouter()


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


@router.post("/objects/put")
def object_put(body: PutObjectIn) -> dict:
    return put_object(body.local_path, body.key, body.bucket)


@router.post("/objects/get")
def object_get(body: GetObjectIn) -> dict:
    return get_object(body.key, body.output_path, body.bucket)


@router.post("/objects/presign")
def object_presign(body: PresignIn) -> dict:
    return presign_get(body.key, body.bucket, body.expires)
