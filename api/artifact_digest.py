from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from api.runtime_ref import to_local_path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def sha256_directory(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(sha256_file(item).encode("utf-8"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def compute_local_artifact_digest(ref: str) -> dict[str, Any]:
    path = to_local_path(ref)
    if path is None:
        return {"ok": False, "reason": "unsupported_ref", "ref": ref, "digest": None}
    if not path.exists():
        return {"ok": False, "reason": "missing_path", "ref": ref, "path": str(path), "digest": None}
    if path.is_dir():
        return {"ok": True, "reason": "directory_hashed", "ref": ref, "path": str(path), "kind": "directory", "digest": sha256_directory(path)}
    return {"ok": True, "reason": "file_hashed", "ref": ref, "path": str(path), "kind": "file", "digest": sha256_file(path)}


def verify_local_artifact_digest(ref: str, expected: str) -> dict[str, Any]:
    result = compute_local_artifact_digest(ref)
    if not result.get("ok"):
        return {**result, "expected": expected, "match": False}
    actual = str(result.get("digest") or "")
    return {**result, "expected": expected, "actual": actual, "match": actual == expected}
