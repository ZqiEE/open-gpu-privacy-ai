from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.artifact_distribution import distribution_metadata, prepare_local_artifact_distribution
from api.candidate_failure_actions import plan_failure_actions
from api.replica_maintenance import run_replica_maintenance_once
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
    location = Path(str(output.get("location") or ""))
    model_path = location / "ngram_model.json"
    if not model_path.exists():
        return None

    artifact_hash = "sha256:" + hashlib.sha256(model_path.read_bytes()).hexdigest()
    backend_ref = model_path.resolve().as_uri()
    source_job_id = str(output.get("source_job_id") or "local-training")
    store = binding_store or ArtifactBindingStore()
    artifact = {
        "artifact_id": f"local_training_{source_job_id}",
        "artifact_hash": artifact_hash,
        "checkpoint_uri": backend_ref,
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
            "mode": "distributed_chunk_manifest",
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
        backend_kind="lightweight-ngram",
        backend_ref=backend_ref,
        status="candidate",
        metadata=metadata,
    )
    gate = evaluate_training_artifact_binding(binding, model_path=model_path, replica_book_path=replica_book_path)
    updated_metadata = {**binding.get("metadata", {}), "promotion_gate": gate}
    if not gate.get("ok"):
        updated_metadata["failure_actions"] = plan_failure_actions(binding, gate, action_path=failure_actions_path)
    binding = store.update_metadata(binding["binding_id"], updated_metadata) or binding
    if gate.get("ok"):
        binding = store.set_status(binding["binding_id"], "active") or binding
    return binding
