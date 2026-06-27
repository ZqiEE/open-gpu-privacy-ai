from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TEXT_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".sql", ".yml", ".yaml", ".toml", ".json", ".txt"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__"}


def stable_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def iter_text_files(root: str | Path, max_bytes: int = 200_000) -> list[dict[str, Any]]:
    base = Path(root)
    items: list[dict[str, Any]] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix and path.suffix not in TEXT_SUFFIXES:
            continue
        if path.stat().st_size > max_bytes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = str(path.relative_to(base))
        items.append({"path": rel, "sha256": stable_id(text), "text": text})
    return items


def build_pack(inputs: list[dict[str, Any]], output: str | Path) -> dict[str, Any]:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    seen: set[str] = set()
    with out.open("w", encoding="utf-8") as fh:
        for item in inputs:
            base = item.get("local_path")
            if not base:
                continue
            for file_item in iter_text_files(base):
                if file_item["sha256"] in seen:
                    continue
                seen.add(file_item["sha256"])
                row = {
                    "schema_version": "ailovanta.code_sample.v1",
                    "repo_id": item.get("repo_id"),
                    "rights_id": item.get("rights_id"),
                    "path": file_item["path"],
                    "sha256": file_item["sha256"],
                    "text": file_item["text"],
                }
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1
    return {"output": str(out), "samples": written}
