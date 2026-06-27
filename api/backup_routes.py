from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.backup_store import BackupStore


router = APIRouter(prefix="/ops/backups", tags=["backups"])
store = BackupStore()


class BackupCreateIn(BaseModel):
    label: str = "manual"
    paths: list[str] | None = None


class RestoreIn(BaseModel):
    dry_run: bool = True


@router.post("")
def create_backup(body: BackupCreateIn = Field(default_factory=BackupCreateIn)) -> dict[str, Any]:
    return store.create(label=body.label, paths=body.paths)


@router.get("")
def list_backups() -> dict[str, Any]:
    return {"items": store.list()}


@router.get("/latest")
def latest_backup_status() -> dict[str, Any]:
    return store.latest_status()


@router.get("/{snapshot_id}/verify")
def verify_backup(snapshot_id: str) -> dict[str, Any]:
    return store.verify(snapshot_id)


@router.post("/{snapshot_id}/restore")
def restore_backup(snapshot_id: str, body: RestoreIn = Field(default_factory=RestoreIn)) -> dict[str, Any]:
    return store.restore(snapshot_id, dry_run=body.dry_run)
