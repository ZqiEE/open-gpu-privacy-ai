from __future__ import annotations

from fastapi import APIRouter

from api.foundation_artifact_ready import check_foundation_artifact_ready

router = APIRouter(prefix="/ops/foundation-artifact", tags=["foundation-artifact"])


@router.get("/ready")
def foundation_artifact_ready(model_key: str | None = None) -> dict:
    return check_foundation_artifact_ready(model_key=model_key)
