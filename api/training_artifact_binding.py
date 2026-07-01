from __future__ import annotations

from pathlib import Path
from typing import Any

from api.artifact_hash import sha256_path
from api.artifact_binding import ArtifactBindingStore
from api.artifact_distribution import distribution_metadata, prepare_local_artifact_distribution
from api.candidate_failure_actions import plan_failure_actions
from api.owned_route_publisher import publish_owned_route_if_active
from api.replica_maintenance import run_replica_maintenance_once
from api.runtime_ref import to_local_path
from api.training_artifact_gate import evaluate_training_artifact_binding


OWNED_MODEL_ID = "ailovanta-owned"
OWNED_VERSION = "candidate"
OWNED_MODEL_KEY = f"{OWNED_MODEL_ID}:{OWNED_VERSION}"
OWNED_MANIFEST_HASH = "sha256:local-owned-candidate"


def bind_local_training_artifact(
    output: dict[str, Any],
    binding_store: ArtifactBindingStore | None = None,
    manifest_dir: str | Path = "runtime_data/artifact_manifests",
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    storage_node_id: str = "local-training-storage",
    auto_repair_replicas: bool = True,
    replica_tasks_path: str | Path = "runtime_data/replica_repair_tasks.json",
    replica_storage_root: str | Path = "runtime_data/storage_replicas",
    failure_actions_path: str | Path = "runtime_data/candidate_failure_actions.json",
) -> dict[str, Any] | None:
    if output.get("status") == "failed":
        return None
    location = Path(str(output.get("location") or ""))
    artifact_info = _resolve_training_artifact(location, output)
    if artifact_info is None:
        return None

    artifact_path = artifact_info["artifact_path"]
    gate_model_path = artifact_info["gate_model_path"]
    artifact_hash = sha256_path(artifact_path)
    backend_ref = artifact_path.resolve().as_uri()
    source_job_id = str(output.get("source_job_id") or "local-training")
    store = binding_store or ArtifactBindingStore()
    artifact = {
        "artifact_id": f"local_training_{source_job_id}",
        "artifact_hash": artifact_hash,
        "checkpoint_uri": backend_ref,
        "artifact_key_id": f"local-training-{source_job_id}",
    }
    distribution = prepare_local_artifact_distribution(
        artifact,
        backend_ref,
        manifest_dir=manifest_dir,
        replica_book_path=replica_book_path,
        storage_node_id=storage_node_id,
    )
    metadata = {
        "source": "local_training_worker",
        "source_job_id": source_job_id,
        "output_location": str(location),
        "backend": (output.get("metrics") or {}).get("backend"),
        "storage_policy": {
            "mode": artifact_info["storage_mode"],
            "anti_theft": "runtime loads by binding and manifest hash; raw artifact path is provenance metadata, not public model access",
        },
    }
    if distribution:
        metadata["artifact_distribution"] = distribution_metadata(distribution)
    replica_maintenance = None
    if distribution and auto_repair_replicas:
        replica_maintenance = run_replica_maintenance_once(tasks_path=replica_tasks_path, replica_book_path=replica_book_path, storage_root=replica_storage_root)
        metadata["replica_maintenance"] = {
            "ok": replica_maintenance.get("ok"),
            "completed_count": replica_maintenance.get("completed_count"),
            "failed_count": replica_maintenance.get("failed_count"),
            "skipped_count": replica_maintenance.get("skipped_count"),
        }

    binding = store.register_binding(
        {
            "model_id": OWNED_MODEL_ID,
            "version": OWNED_VERSION,
            "model_key": OWNED_MODEL_KEY,
            "manifest_hash": OWNED_MANIFEST_HASH,
            "status": "candidate",
        },
        artifact,
        backend_kind=artifact_info["backend_kind"],
        backend_ref=backend_ref,
        status="candidate",
        metadata=metadata,
    )
    gate = evaluate_training_artifact_binding(binding, model_path=gate_model_path, replica_book_path=replica_book_path)
    updated_metadata = {**binding.get("metadata", {}), "promotion_gate": gate}
    if not gate.get("ok"):
        updated_metadata["failure_actions"] = plan_failure_actions(binding, gate, action_path=failure_actions_path)
    binding = store.update_metadata(binding["binding_id"], updated_metadata) or binding
    if gate.get("ok"):
        binding = store.set_status(binding["binding_id"], "active") or binding
        route_publish = publish_owned_route_if_active(binding, bindings=store)
        binding = _append_route_publish_metadata(store, binding, route_publish)
    return binding


def attach_training_worker_receipt(
    binding: dict[str, Any],
    receipt: dict[str, Any] | None,
    binding_store: ArtifactBindingStore | None = None,
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    failure_actions_path: str | Path = "runtime_data/candidate_failure_actions.json",
) -> dict[str, Any] | None:
    if not binding or not receipt:
        return binding
    store = binding_store or ArtifactBindingStore()
    model_path = _gate_model_path_for_binding(binding)
    if model_path is None:
        return binding

    metadata = {
        **(binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}),
        "training_worker_receipt": _compact_training_worker_receipt(receipt),
    }
    updated = store.update_metadata(binding["binding_id"], metadata) or {**binding, "metadata": metadata}
    gate = evaluate_training_artifact_binding(updated, model_path=model_path, replica_book_path=replica_book_path)
    updated_metadata = {**(updated.get("metadata") if isinstance(updated.get("metadata"), dict) else {}), "promotion_gate": gate}
    if not gate.get("ok"):
        updated_metadata["failure_actions"] = plan_failure_actions(updated, gate, action_path=failure_actions_path)
    updated = store.update_metadata(updated["binding_id"], updated_metadata) or {**updated, "metadata": updated_metadata}
    if gate.get("ok"):
        updated = store.set_status(updated["binding_id"], "active") or updated
        route_publish = publish_owned_route_if_active(updated, bindings=store)
        updated = _append_route_publish_metadata(store, updated, route_publish)
    return updated


def _resolve_training_artifact(location: Path, output: dict[str, Any]) -> dict[str, Any] | None:
    ngram_path = location / "ngram_model.json"
    if ngram_path.exists():
        return {
            "artifact_path": ngram_path,
            "gate_model_path": ngram_path,
            "backend_kind": "lightweight-ngram",
            "storage_mode": "distributed_chunk_manifest",
        }

    output_record_path = location / "output.json"
    backend = str((output.get("metrics") or {}).get("backend") or "")
    if location.exists() and location.is_dir() and output_record_path.exists() and backend in {"transformers", "lora", "qlora"}:
        return {
            "artifact_path": location,
            "gate_model_path": output_record_path,
            "backend_kind": "transformers-local",
            "storage_mode": "sealed_distributed_model_directory_manifest",
        }
    return None


def _gate_model_path_for_binding(binding: dict[str, Any]) -> Path | None:
    metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
    output_location = Path(str(metadata.get("output_location") or ""))
    backend_kind = str(binding.get("backend_kind") or "")
    if backend_kind == "lightweight-ngram":
        candidate = output_location / "ngram_model.json"
        return candidate if candidate.exists() else None
    if backend_kind in {"transformers-local", "transformers-causal-lm"}:
        candidate = output_location / "output.json"
        if candidate.exists():
            return candidate
    backend_path = to_local_path(str(binding.get("backend_ref") or binding.get("checkpoint_uri") or ""))
    if backend_path and backend_path.is_dir() and (backend_path / "output.json").exists():
        return backend_path / "output.json"
    if backend_path and backend_path.is_file():
        return backend_path
    return None


def _compact_training_worker_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "schema_version",
        "receipt_id",
        "result_hash",
        "node_id",
        "job_id",
        "artifact_hash",
        "artifact_binding_id",
        "passed",
        "score",
        "blockers",
        "receipt_hash",
        "created_at",
    ]
    return {key: receipt.get(key) for key in keys if key in receipt}


def _append_route_publish_metadata(store: ArtifactBindingStore, binding: dict[str, Any], route_publish: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        **(binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}),
        "route_publish": _compact_route_publish(route_publish),
    }
    return store.update_metadata(binding["binding_id"], metadata) or {**binding, "metadata": metadata}


def _compact_route_publish(route_publish: dict[str, Any]) -> dict[str, Any]:
    route = route_publish.get("route") if isinstance(route_publish.get("route"), dict) else {}
    return {
        "ok": route_publish.get("ok"),
        "reason": route_publish.get("reason"),
        "route_key": route.get("route_key"),
        "model_key": route.get("model_key"),
        "binding_id": route.get("binding_id"),
        "status": route.get("status"),
    }
