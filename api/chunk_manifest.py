from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ChunkRef:
    chunk_id: str
    size_bytes: int
    sha256: str
    sources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactManifest:
    artifact_id: str
    artifact_hash: str
    chunks: list[ChunkRef]
    replica_policy: dict[str, Any]
    schema_version: str = "ailovanta.artifact_manifest.v1"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "artifact_id": self.artifact_id, "artifact_hash": self.artifact_hash, "chunks": [chunk.to_dict() for chunk in self.chunks], "replica_policy": self.replica_policy}


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def manifest_hash(manifest: dict[str, Any]) -> str:
    body = {key: value for key, value in manifest.items() if key != "manifest_hash"}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def build_manifest(path: str | Path, chunk_size: int = 8 * 1024 * 1024, sources: list[str] | None = None, min_replicas: int = 3) -> dict[str, Any]:
    artifact_path = Path(path)
    data_hash = hashlib.sha256()
    chunks: list[ChunkRef] = []
    with artifact_path.open("rb") as handle:
        index = 0
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            data_hash.update(data)
            chunks.append(ChunkRef(chunk_id=f"chunk_{index:06d}", size_bytes=len(data), sha256=sha256_bytes(data), sources=sources or [str(artifact_path)]))
            index += 1
    manifest = ArtifactManifest(
        artifact_id="artifact_" + uuid4().hex[:12],
        artifact_hash="sha256:" + data_hash.hexdigest(),
        chunks=chunks,
        replica_policy={"min_replicas": min_replicas, "source_types": ["node_cache", "regional_mirror", "content_addressed", "official_seed_fallback"]},
    )
    payload = manifest.to_dict()
    payload["manifest_hash"] = manifest_hash(payload)
    return payload


def write_manifest(path: str | Path, output: str | Path) -> dict[str, Any]:
    manifest = build_manifest(path)
    Path(output).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
