from __future__ import annotations

from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.route_policy import check_route


def apply_gate(model_id: str, version: str, request_id: str, store: ArtifactBindingStore | None = None) -> dict[str, Any] | None:
    return check_route(model_id, f"{model_id}:{version}", request_id, store)
