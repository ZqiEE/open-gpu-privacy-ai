from __future__ import annotations

from fastapi import APIRouter

from api.readiness_audit import ReadinessAudit


router = APIRouter()
audit = ReadinessAudit()


@router.get("/ops/readiness")
def readiness() -> dict:
    return audit.production_check()


@router.get("/ops/readiness/catalog")
def readiness_catalog(status: str | None = "published") -> dict:
    return audit.check_catalog(status=status)


@router.get("/ops/readiness/manifests")
def readiness_manifests() -> dict:
    return audit.check_manifests()
