from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.asset_lookup import file_path


class ModelAssetStore:
    def __init__(self, root: str = "runtime_data/assets") -> None:
        self.root = root

    def put(self, payload: dict[str, Any]) -> dict:
        digest = str(payload.get("artifact_hash") or payload.get("manifest_hash") or "")
        if not digest:
            raise ValueError("missing asset digest")
        path = file_path(digest, self.root)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.get(digest) or {}

    def get(self, digest: str) -> dict | None:
        path = file_path(digest, self.root)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {"digest": digest, "path": str(path), "payload": payload}

    def list(self, limit: int = 50) -> list[dict]:
        root = Path(self.root)
        if not root.exists():
            return []
        items = []
        for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            items.append({"path": str(path), "payload": payload})
        return items
