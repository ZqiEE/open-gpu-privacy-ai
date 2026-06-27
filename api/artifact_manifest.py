from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any


SCHEMA = "ailovanta.artifact_manifest.v1"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def build_chunk_manifest(path: str | Path, artifact_uri: str, chunk_size: int = 8 * 1024 * 1024, replicas: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(str(source))
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    chunks: list[dict[str, Any]] = []
    with source.open("rb") as handle:
        index = 0
        offset = 0
        while True:
            data = handle.read(chunk_size)
            if not data:
                break
            chunk_uri = f"{artifact_uri}#chunk={index}"
            chunks.append({
                "index": index,
                "offset": offset,
                "size_bytes": len(data),
                "chunk_hash": sha256_bytes(data),
                "sources": [chunk_uri, *(replicas or [])],
            })
            offset += len(data)
            index += 1
    return {
        "schema_version": SCHEMA,
        "artifact_uri": artifact_uri,
        "artifact_hash": sha256_file(source),
        "size_bytes": source.stat().st_size,
        "chunk_size": chunk_size,
        "chunk_count": len(chunks),
        "chunks": chunks,
        "metadata": metadata or {},
        "created_at": round(time(), 3),
    }


def write_chunk_manifest(path: str | Path, artifact_uri: str, output_path: str | Path, chunk_size: int = 8 * 1024 * 1024, replicas: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = build_chunk_manifest(path, artifact_uri, chunk_size=chunk_size, replicas=replicas, metadata=metadata)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def verify_chunk_manifest(manifest: dict[str, Any], path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        return {"ok": False, "reason": "artifact_file_missing"}
    expected_artifact_hash = manifest.get("artifact_hash")
    actual_artifact_hash = sha256_file(source)
    blockers: list[str] = []
    if expected_artifact_hash != actual_artifact_hash:
        blockers.append("artifact_hash_mismatch")
    chunk_size = int(manifest.get("chunk_size") or 0)
    if chunk_size <= 0:
        blockers.append("bad_chunk_size")
    checked_chunks: list[dict[str, Any]] = []
    if chunk_size > 0:
        with source.open("rb") as handle:
            for chunk in manifest.get("chunks", []):
                index = int(chunk.get("index"))
                data = handle.read(chunk_size)
                actual = sha256_bytes(data)
                ok = actual == chunk.get("chunk_hash")
                checked_chunks.append({"index": index, "ok": ok, "expected": chunk.get("chunk_hash"), "actual": actual})
                if not ok:
                    blockers.append(f"chunk_hash_mismatch:{index}")
    return {"ok": not blockers, "blockers": sorted(set(blockers)), "artifact_hash": actual_artifact_hash, "chunks": checked_chunks}
