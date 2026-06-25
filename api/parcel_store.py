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

    def put_many(self, group_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not group_id or not items:
            raise ValueError("missing input")
        for item in items:
            item_id = item.get("id")
            if not item_id:
                raise ValueError("missing item id")
            payload = {**item, "group_id": group_id, "status": item.get("status", "open")}
            self._write(self.inbox / f"{item_id}.json", payload)
        return {"group_id": group_id, "count": len(items)}

    def list_inbox(self) -> list[dict[str, Any]]:
        return [self._read(path) for path in sorted(self.inbox.glob("*.json"))]

    def put_outbox(self, payload: dict[str, Any]) -> dict[str, Any]:
        item_id = payload.get("id")
        if not item_id:
            raise ValueError("missing output id")
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
