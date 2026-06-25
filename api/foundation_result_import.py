from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.chain_registry import ChainRegistry
from api.core_result_store import CoreResultStore
from api.runtime_ref import check_runtime_ref
from api.runtime_store import RuntimeStore


def load_foundation_result(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_foundation_result(payload)
    return payload


def validate_foundation_result(payload: dict[str, Any]) -> None:
    if not payload.get("plan"):
        raise ValueError("missing foundation plan")
    if not payload.get("artifact"):
        raise ValueError("missing foundation artifact")
    artifact = payload["artifact"]
    for key in ["artifact_hash", "model_id", "version", "source_plan_id"]:
        if not artifact.get(key):
            raise ValueError(f"missing artifact field: {key}")


def foundation_result_to_core_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    validate_foundation_result(payload)
    artifact = payload["artifact"]
    plan = payload["plan"]
    return {
        "schema_version": "ailovanta.core_result.v1",
        "source_job_id": artifact["source_plan_id"],
        "round_id": artifact["artifact_id"],
        "accepted_candidates": 1,
        "next_model_version": artifact["version"],
        "base_model": plan.get("model", {}).get("model_id", "ailovanta-owned"),
        "dataset_uri": "foundation://" + artifact["source_plan_id"],
        "summary_path": artifact.get("backend_ref") or artifact.get("checkpoint_uri", ""),
        "promotion_status": artifact.get("promotion_status", "candidate"),
        "artifact": artifact,
    }


def set_runtime_model_status(runtime: RuntimeStore, model_key: str, status: str) -> dict[str, Any]:
    with runtime.connect() as conn:
        before = conn.execute("SELECT status FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
        conn.execute("UPDATE runtime_models SET status = ? WHERE model_key = ?", (status, model_key))
        after = conn.execute("SELECT status FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
    return {"model_key": model_key, "before": before[0] if before else None, "after": after[0] if after else None, "found": after is not None}


def import_foundation_result(
    payload: dict[str, Any],
    core_results: CoreResultStore | None = None,
    runtime_store: RuntimeStore | None = None,
    chain_registry: ChainRegistry | None = None,
    binding_store: ArtifactBindingStore | None = None,
) -> dict[str, Any]:
    core_store = core_results or CoreResultStore()
    runtime = runtime_store or RuntimeStore()
    chain = chain_registry or ChainRegistry()
    bindings = binding_store or ArtifactBindingStore()

    manifest = foundation_result_to_core_manifest(payload)
    core_result = core_store.register_manifest(manifest)
    runtime_result = core_store.promote_to_runtime(core_result["result_id"], runtime)
    runtime_model = runtime_result["runtime_model"]
    artifact = manifest["artifact"]
    backend_ref = artifact.get("backend_ref") or artifact.get("checkpoint_uri", "")
    initial_status = "active" if runtime_model.get("status") == "active" else "candidate"
    binding = bindings.register_binding(
        runtime_model,
        artifact,
        backend_kind=artifact.get("backend_kind", "checkpoint-artifact"),
        backend_ref=backend_ref,
        status=initial_status,
        metadata={"core_result_id": core_result["result_id"], "source": "foundation_import", "backend_ref_source": "artifact.backend_ref" if artifact.get("backend_ref") else "artifact.checkpoint_uri"},
    )
    ref_check = check_runtime_ref(binding)
    runtime_status_update = None
    if not ref_check["ready"]:
        binding = bindings.set_status(binding["binding_id"], "unavailable") or binding
        runtime_status_update = set_runtime_model_status(runtime, runtime_model["model_key"], "unavailable")
        runtime_model = runtime.get_model(runtime_model["model_key"]) or runtime_model
    chain_event = chain.append_model_event(
        {
            "event_type": "model_artifact_promoted",
            "model_id": runtime_model["model_id"],
            "version": runtime_model["version"],
            "artifact_hash": artifact["artifact_hash"],
            "runtime_manifest_hash": runtime_model["manifest_hash"],
            "metadata": {"core_result_id": core_result["result_id"], "artifact_id": artifact["artifact_id"], "binding_id": binding["binding_id"], "backend_ref": backend_ref, "ref_ready": ref_check["ready"], "ref_reason": ref_check["reason"], "runtime_status_update": runtime_status_update},
        }
    )
    return {"core_result": core_result, "runtime_model": runtime_model, "artifact_binding": binding, "runtime_ref_check": ref_check, "runtime_status_update": runtime_status_update, "chain_event": chain_event}


def import_foundation_result_file(path: str | Path) -> dict[str, Any]:
    return import_foundation_result(load_foundation_result(path))
