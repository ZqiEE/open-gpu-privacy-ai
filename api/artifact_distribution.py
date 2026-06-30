from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.chunk_manifest import build_manifest
from api.replica_book import add_manifest, status as replica_status
from api.runtime_ref import to_local_path
from api.secure_artifact_pack import SecureArtifactError, package_secure_model_directory


def prepare_local_artifact_distribution(
    artifact: dict[str, Any],
    backend_ref: str,
    manifest_dir: str | Path = "runtime_data/artifact_manifests",
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    storage_node_id: str = "local-storage",
) -> dict[str, Any] | None:
    path = to_local_path(backend_ref or artifact.get("checkpoint_uri", ""))
    if not path or not path.exists():
        return None
    if path.is_dir():
        try:
            packaged = package_secure_model_directory(
                path,
                manifest_dir=manifest_dir,
                replica_book_path=replica_book_path,
                storage_node_id=storage_node_id,
                key_id=str(artifact.get("artifact_key_id") or "artifact-binding-key"),
            )
        except SecureArtifactError:
            return None
        manifest = packaged["manifest"]
        return {
            "schema_version": "ailovanta.artifact_distribution.v1",
            "artifact_id": artifact["artifact_id"],
            "model_artifact_hash": artifact["artifact_hash"],
            "storage_artifact_hash": manifest["artifact_hash"],
            "plaintext_artifact_hash": manifest.get("plaintext_artifact_hash"),
            "manifest_hash": manifest["manifest_hash"],
            "manifest_uri": packaged["manifest_uri"],
            "manifest": manifest,
            "replica_book_path": str(Path(replica_book_path)),
            "replica_status": replica_status(replica_book_path),
            "hash_matches_model_artifact": manifest["artifact_hash"] == artifact["artifact_hash"],
            "sealed": True,
            "anti_theft": manifest.get("anti_theft"),
            "book": packaged["book"],
        }
    if not path.is_file():
        return None
    manifest = build_manifest(path, sources=[f"node://{storage_node_id}/{path.name}"])
    out_dir = Path(manifest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / f"{artifact['artifact_id']}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    book = add_manifest(manifest, node_id=storage_node_id, location="file://" + str(path), path=replica_book_path)
    return {
        "schema_version": "ailovanta.artifact_distribution.v1",
        "artifact_id": artifact["artifact_id"],
        "model_artifact_hash": artifact["artifact_hash"],
        "storage_artifact_hash": manifest["artifact_hash"],
        "manifest_hash": manifest["manifest_hash"],
        "manifest_uri": "file://" + str(manifest_path.resolve()),
        "manifest": manifest,
        "replica_book_path": str(Path(replica_book_path)),
        "replica_status": replica_status(replica_book_path),
        "hash_matches_model_artifact": manifest["artifact_hash"] == artifact["artifact_hash"],
        "book": book,
    }


def distribution_metadata(distribution: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in distribution.items() if key != "book"}
