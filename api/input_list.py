from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class InputList:
    def __init__(self, path: str | Path = "runtime_data/input_list.json") -> None:
        self.path = Path(path)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        return list(payload.get("items") or [])

    def write(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, item: dict[str, Any]) -> dict[str, Any]:
        items = self.read()
        items.append(dict(item))
        self.write(items)
        return items[-1]
