from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from api.artifact_binding import ArtifactBindingStore


OWNED_MODEL_ID = "ailovanta-owned"
OWNED_VERSION = "candidate"
OWNED_MODEL_KEY = f"{OWNED_MODEL_ID}:{OWNED_VERSION}"
OWNED_MANIFEST_HASH = "sha256:local-owned-candidate"


def bind_local_training_artifact(
    output: dict[str, Any],
    binding_store: ArtifactBindingStore | None = None,
) -> dict[str, Any] | None:
    location = Path(str(output.get("location") or ""))
    model_path = location / "ngram_model.json"
    if not model_path.exists():
        return None

    artifact_hash = "sha256:" + hashlib.sha256(model_path.read_bytes()).hexdigest()
    backend_ref = "file://" + str(model_path.resolve())
    source_job_id = str(output.get("source_job_id") or "local-training")
    store = binding_store or ArtifactBindingStore()
    return store.register_binding(
        {
            "model_id": OWNED_MODEL_ID,
            "version": OWNED_VERSION,
            "model_key": OWNED_MODEL_KEY,
            "manifest_hash": OWNED_MANIFEST_HASH,
            "status": "active",
        },
        {
            "artifact_id": f"local_training_{source_job_id}",
            "artifact_hash": artifact_hash,
            "checkpoint_uri": backend_ref,
        },
        backend_kind="lightweight-ngram",
        backend_ref=backend_ref,
        status="active",
        metadata={
            "source": "local_training_worker",
            "source_job_id": source_job_id,
            "output_location": str(location),
            "backend": (output.get("metrics") or {}).get("backend"),
        },
    )
