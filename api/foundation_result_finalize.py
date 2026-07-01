from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.artifact_digest import compute_local_artifact_digest


def finalize_foundation_result(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("plan"):
        raise ValueError("missing foundation plan")
    artifact = dict(payload.get("artifact") or {})
    plan = payload["plan"]
    model = plan.get("model") or {}

    artifact.setdefault("schema_version", "ailovanta.foundation_artifact.v1")
    artifact.setdefault("model_id", model.get("model_id", "ailovanta-owned"))
    artifact.setdefault("version", model.get("target_version", "candidate"))
    artifact.setdefault("source_plan_id", plan.get("plan_id", "foundation_plan"))
    artifact.setdefault("promotion_status", "candidate")

    backend_ref = artifact.get("backend_ref") or artifact.get("checkpoint_uri")
    if not backend_ref:
        raise ValueError("missing artifact backend_ref or checkpoint_uri")
    artifact["backend_ref"] = backend_ref
    artifact.setdefault("checkpoint_uri", backend_ref)

    digest = compute_local_artifact_digest(str(backend_ref))
    if not digest.get("ok"):
        raise ValueError("artifact digest unavailable: " + str(digest.get("reason")))
    artifact["artifact_hash"] = str(digest["digest"])
    artifact.setdefault("artifact_id", "foundation_artifact_" + str(digest["digest"]).removeprefix("sha256:")[:12])
    metadata = dict(artifact.get("metadata") or {})
    metadata["finalized_by"] = "foundation_result_finalize"
    metadata["digest_reason"] = digest.get("reason")
    metadata["digest_kind"] = digest.get("kind")
    metadata["digest_path"] = digest.get("path")
    artifact["metadata"] = metadata

    return {**payload, "artifact": artifact}


def finalize_foundation_result_file(path: str | Path, write: bool = True) -> dict[str, Any]:
    result_path = Path(path)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    finalized = finalize_foundation_result(payload)
    if write:
        result_path.write_text(json.dumps(finalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return finalized
