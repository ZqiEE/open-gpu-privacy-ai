from __future__ import annotations

from pathlib import Path


def index_root(root: str = "runtime_data/assets") -> Path:
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_name(digest: str) -> str:
    safe = digest.replace(":", "_").replace("/", "_")
    return safe + ".json"


def file_path(digest: str, root: str = "runtime_data/assets") -> Path:
    return index_root(root) / file_name(digest)
