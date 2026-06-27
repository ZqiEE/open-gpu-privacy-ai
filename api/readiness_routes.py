from __future__ import annotations

from fastapi import APIRouter

from api.artifact_integrity import verify_artifact_uri
from api.catalog import Catalog
from api.readiness_audit import ReadinessAudit


router = APIRouter()
audit = ReadinessAudit()
catalog = Catalog()


@router.get("/ops/readiness")
def readiness(verify_bytes: bool = False) -> dict:
    return audit.production_check(verify_bytes=verify_bytes)


@router.get("/ops/readiness/catalog")
def readiness_catalog(status: str | None = "published", verify_bytes: bool = False) -> dict:
    return audit.check_catalog(status=status, verify_bytes=verify_bytes)


@router.get("/ops/readiness/manifests")
def readiness_manifests() -> dict:
    return audit.check_manifests()


@router.get("/ops/artifacts/verify")
def verify_artifact(uri: str, expected_hash: str) -> dict:
    return verify_artifact_uri(uri, expected_hash)


@router.get("/ops/artifacts/verify-catalog/{item_id}")
def verify_catalog_artifact(item_id: str) -> dict:
    item = catalog.get(item_id)
    if not item:
        return {"ok": False, "reason": "item_not_found", "item_id": item_id}
    uri = str(item.get("artifact_uri") or item.get("location") or "")
    expected = str(item.get("artifact_hash") or item.get("digest") or "")
    return verify_artifact_uri(uri, expected)
