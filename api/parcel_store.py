from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ParcelStore:
    def __init__(self, root: str | Path = "runtime_data/parcels") -> None:
        self.root = Path(root)
        self.inbox = self.root / "inbox"
        self.outbox = self.root / "outbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def item_id(payload: dict[str, Any]) -> str:
        item_id = payload.get("id") or payload.get("task_id") or payload.get("result_id")
        if not item_id and isinstance(payload.get("task"), dict):
            item_id = payload["task"].get("task_id") or payload["task"].get("id")
        if not item_id:
            raise ValueError("missing item id")
        return str(item_id)

    def put_many(self, group_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not group_id or not items:
            raise ValueError("missing input")
        for item in items:
            item_id = self.item_id(item)
            payload = {**item, "id": item.get("id") or item_id, "group_id": group_id, "status": item.get("status", "open")}
            self._write(self.inbox / f"{item_id}.json", payload)
        return {"group_id": group_id, "count": len(items)}

    def get_inbox(self, item_id: str) -> dict[str, Any] | None:
        path = self.inbox / f"{item_id}.json"
        return self._read(path) if path.exists() else None

    def list_inbox(self, node_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        items = [self._read(path) for path in sorted(self.inbox.glob("*.json"))]
        if node_id:
            items = [item for item in items if (item.get("node_id") or item.get("task", {}).get("node_id")) == node_id]
        if status:
            items = [item for item in items if item.get("status") == status]
        return items

    def update_inbox(self, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        item = self.get_inbox(item_id)
        if not item:
            return None
        item.update(patch)
        self._write(self.inbox / f"{item_id}.json", item)
        return item

    def put_outbox(self, payload: dict[str, Any]) -> dict[str, Any]:
        item_id = self.item_id(payload)
        payload = {**payload, "id": payload.get("id") or item_id}
        self._write(self.outbox / f"{item_id}.json", payload)
        return payload

    def list_outbox(self) -> list[dict[str, Any]]:
        return [self._read(path) for path in sorted(self.outbox.glob("*.json"))]

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
