from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_path(path: str | Path) -> str:
    target = Path(path)
    if target.is_file():
        return "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
    if target.is_dir():
        return _sha256_directory(target)
    raise FileNotFoundError(str(target))


def _sha256_directory(root: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = item.relative_to(root).as_posix().encode("utf-8")
        content_hash = hashlib.sha256(item.read_bytes()).hexdigest().encode("ascii")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(item.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(content_hash)
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()
