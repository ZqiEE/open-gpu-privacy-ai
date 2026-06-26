from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from api.pool_store import get, info, load_manifest, put

router = APIRouter(prefix="/storage-pool", tags=["storage-pool"])


class ManifestBody(BaseModel):
    manifest: str | None = None
    output: str | None = None


def newest_manifest(root: str | Path = "runtime_data/manifests") -> Path | None:
    folder = Path(root)
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def read_manifest(value: str | None) -> dict:
    path = Path(value) if value else newest_manifest()
    if not path or not path.exists():
        raise RuntimeError("manifest not found")
    return load_manifest(path)


@router.get("/status")
def status() -> dict:
    return info()


@router.post("/put")
def put_artifact(body: ManifestBody) -> dict:
    try:
        return put(read_manifest(body.manifest))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/get")
def get_artifact(body: ManifestBody) -> dict:
    if not body.output:
        return {"ok": False, "error": "output is required"}
    try:
        return get(read_manifest(body.manifest), body.output)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
