from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.content_addressing import content_id, hash_object


class LocalObjectStoreAdapter:
    name = "local-object-store"

    def __init__(self, root: str | Path = "runtime_data/object_store") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_json(self, value: Any, prefix: str = "obj") -> dict:
        obj_hash = hash_object(value)
        obj_id = content_id(value, prefix=prefix)
        path = self.root / f"{obj_id}.json"
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"object_id": obj_id, "hash": obj_hash, "path": str(path), "adapter": self.name}

    def get_json(self, object_id: str) -> Any:
        path = self.root / f"{object_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def status(self) -> dict:
        return {"adapter": self.name, "root": str(self.root), "objects": len(list(self.root.glob("*.json")))}
