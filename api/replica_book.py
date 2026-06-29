from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BOOK = Path("runtime_data/replica_book.json")


def load(path: Path = BOOK) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "ailovanta.replica_book.v1", "artifacts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save(data: dict[str, Any], path: Path = BOOK) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def add_manifest(manifest: dict[str, Any], node_id: str = "local", location: str | None = None, path: str | Path = BOOK) -> dict[str, Any]:
    book_path = Path(path)
    data = load(book_path)
    ah = manifest["artifact_hash"]
    replica_policy = manifest.get("replica_policy") if isinstance(manifest.get("replica_policy"), dict) else {}
    artifact = data.setdefault(
        "artifacts",
        {},
    ).setdefault(
        ah,
        {
            "artifact_hash": ah,
            "artifact_id": manifest.get("artifact_id"),
            "artifact_name": manifest.get("artifact_name"),
            "artifact_bytes": manifest.get("artifact_bytes"),
            "manifest_hash": manifest.get("manifest_hash"),
            "min_replicas": manifest.get("min_replicas") or replica_policy.get("min_replicas", 3),
            "chunks": {},
        },
    )
    for chunk in manifest.get("chunks", []):
        ch = chunk.get("hash") or chunk.get("sha256") or chunk.get("chunk_hash")
        if not ch:
            continue
        sources = chunk.get("sources") if isinstance(chunk.get("sources"), list) else []
        rec = artifact.setdefault("chunks", {}).setdefault(ch, {"index": chunk.get("index") or chunk.get("chunk_id"), "bytes": chunk.get("bytes") or chunk.get("size_bytes"), "copies": []})
        copy = {"node_id": node_id, "location": location or chunk.get("source") or (sources[0] if sources else ""), "status": "available"}
        if copy not in rec["copies"]:
            rec["copies"].append(copy)
    return save(data, book_path)


def add_copy(artifact_hash: str, chunk_hash: str, node_id: str, location: str, path: str | Path = BOOK, copy_status: str = "available") -> dict[str, Any]:
    book_path = Path(path)
    data = load(book_path)
    artifact = data.setdefault("artifacts", {}).get(artifact_hash)
    if not artifact:
        raise ValueError("artifact not found in replica book")
    chunk = artifact.setdefault("chunks", {}).get(chunk_hash)
    if not chunk:
        raise ValueError("chunk not found in replica book")
    copy = {"node_id": node_id, "location": location, "status": copy_status}
    copies = chunk.setdefault("copies", [])
    if copy not in copies:
        copies.append(copy)
    return save(data, book_path)


def under_replicated(path: str | Path = BOOK, artifact_hash: str | None = None) -> list[dict[str, Any]]:
    data = load(Path(path))
    rows: list[dict[str, Any]] = []
    for ah, artifact in data.get("artifacts", {}).items():
        if artifact_hash and ah != artifact_hash:
            continue
        need = int(artifact.get("min_replicas") or 1)
        for chunk_hash, chunk in artifact.get("chunks", {}).items():
            copies = chunk.get("copies", []) if isinstance(chunk.get("copies"), list) else []
            available = [copy for copy in copies if copy.get("status") == "available"]
            missing = max(0, need - len(available))
            if missing:
                rows.append(
                    {
                        "artifact_hash": ah,
                        "artifact_id": artifact.get("artifact_id"),
                        "artifact_name": artifact.get("artifact_name"),
                        "manifest_hash": artifact.get("manifest_hash"),
                        "chunk_hash": chunk_hash,
                        "chunk_index": chunk.get("index"),
                        "bytes": chunk.get("bytes"),
                        "min_replicas": need,
                        "available_replicas": len(available),
                        "missing_replicas": missing,
                        "copies": copies,
                    }
                )
    return rows


def status(path: str | Path = BOOK) -> dict[str, Any]:
    data = load(Path(path))
    rows = []
    for ah, artifact in data.get("artifacts", {}).items():
        need = int(artifact.get("min_replicas") or 1)
        chunks = artifact.get("chunks", {})
        weak = [ch for ch, rec in chunks.items() if len(rec.get("copies", [])) < need]
        rows.append({"artifact_hash": ah, "artifact_name": artifact.get("artifact_name"), "chunk_count": len(chunks), "under_replicated_chunks": len(weak), "healthy": not weak})
    return {"artifact_count": len(rows), "artifacts": rows}
