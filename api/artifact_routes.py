from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.artifact_fetch import fetch_artifact


router = APIRouter()


class ArtifactFetchIn(BaseModel):
    url: str
    output_dir: str = "runtime_data/artifacts"
    expected_sha256: str | None = None


@router.post("/artifacts/fetch")
def fetch_remote_artifact(body: ArtifactFetchIn) -> dict:
    return fetch_artifact(body.url, body.output_dir, body.expected_sha256)
