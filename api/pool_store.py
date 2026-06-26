from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from api.ckpt_merge import to_path

ROOT = Path("runtime_data/storage_pool")
CHUNKS = ROOT / "chunks"


def raw_hash(value: str) -> str:
    return value.replace("sha256:", "")


def slot(value: str, root: Path = CHUNKS) -> Path:
    raw = raw_hash(value)
    return root / raw[:2] / raw[2:]


def put(manifest: dict[str, Any], root: Path = CHUNKS) -> dict[str, Any]:
    src = to_path(str(manifest.get("artifact_ref") or ""))
    if src is None or not src.exists():
        raise RuntimeError("artifact source not found")
    root.mkdir(parents=True, exist_ok=True)
    written = 0
    with src.open("rb") as fh:
        for part in manifest.get("chunks", []):
            data = fh.read(int(part["bytes"]))
            digest = "sha256:" + hashlib.sha256(data).hexdigest()
            if digest != part["hash"]:
                raise RuntimeError("part hash mismatch")
            target = slot(digest, root)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(data)
                written += 1
    return {"ok": True, "artifact_hash": manifest.get("artifact_hash"), "parts": len(manifest.get("chunks", [])), "written": written, "root": str(root)}


def get(manifest: dict[str, Any], output: str | Path, root: Path = CHUNKS) -> dict[str, Any]:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    full = hashlib.sha256()
    with out.open("wb") as fh:
        for part in sorted(manifest.get("chunks", []), key=lambda x: int(x.get("index", 0))):
            path = slot(part["hash"], root)
            if not path.exists():
                raise RuntimeError("missing part " + part["hash"])
            data = path.read_bytes()
            digest = "sha256:" + hashlib.sha256(data).hexdigest()
            if digest != part["hash"]:
                raise RuntimeError("stored part mismatch")
            full.update(data)
            fh.write(data)
    digest = "sha256:" + full.hexdigest()
    if digest != manifest.get("artifact_hash"):
        raise RuntimeError("artifact mismatch")
    return {"ok": True, "output": str(out), "artifact_hash": digest, "bytes": out.stat().st_size}


def info(root: Path = CHUNKS) -> dict[str, Any]:
    if not root.exists():
        return {"parts": 0, "bytes": 0, "root": str(root)}
    files = [p for p in root.rglob("*") if p.is_file()]
    return {"parts": len(files), "bytes": sum(p.stat().st_size for p in files), "root": str(root)}


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
