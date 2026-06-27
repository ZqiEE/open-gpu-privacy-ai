from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class Catalog:
    def __init__(self, path: str | Path = "runtime_data/catalog.json", manifest_dir: str | Path = "runtime_data/manifests") -> None:
        self.path = Path(path)
        self.manifest_dir = Path(manifest_dir)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        items = json.loads(self.path.read_text(encoding="utf-8"))
        if status:
            items = [item for item in items if item.get("status") == status]
        return items

    def add(self, body: dict[str, Any]) -> dict[str, Any]:
        items = self.list()
        item = {
            "id": body.get("id") or "item_" + uuid4().hex[:12],
            "name": body["name"],
            "version": body["version"],
            "source_job_id": body.get("source_job_id", "manual"),
            "location": body["location"],
            "artifact_uri": body.get("artifact_uri") or body.get("location"),
            "artifact_hash": body.get("artifact_hash") or body.get("digest"),
            "artifact_manifest": body.get("artifact_manifest") or (body.get("metrics", {}) or {}).get("artifact_manifest"),
            "kind": body.get("kind", "adapter"),
            "digest": body.get("digest") or self.digest(body),
            "metrics": body.get("metrics", {}),
            "proof": body.get("proof") or body.get("node_proof") or body.get("receipt"),
            "anchor_receipt": body.get("anchor_receipt"),
            "status": body.get("status", "candidate"),
            "notes": body.get("notes", ""),
        }
        items = [old for old in items if not (old["name"] == item["name"] and old["version"] == item["version"])]
        items.append(item)
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        return item

    def get(self, item_id: str) -> dict[str, Any] | None:
        for item in self.list():
            if item["id"] == item_id:
                return item
        return None

    def patch(self, item_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        items = self.list()
        found = None
        for item in items:
            if item["id"] == item_id:
                item.update(patch)
                found = item
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        return found

    def set_status(self, item_id: str, status: str) -> dict[str, Any] | None:
        return self.patch(item_id, {"status": status})

    def write_manifest(self, item: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
        manifest = {
            "schema": "ailovanta.runtime_manifest.v1",
            "name": item["name"],
            "version": item["version"],
            "catalog_id": item["id"],
            "source_job_id": item["source_job_id"],
            "location": item["location"],
            "artifact_uri": item.get("artifact_uri") or item["location"],
            "artifact_hash": item.get("artifact_hash") or item.get("digest"),
            "artifact_manifest": item.get("artifact_manifest"),
            "kind": item["kind"],
            "digest": item["digest"],
            "metrics": item["metrics"],
            "proof": item.get("proof"),
            "anchor_receipt": item.get("anchor_receipt"),
            "route": route,
        }
        path = self.manifest_dir / f"{item['name']}--{item['version']}.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"path": str(path), "manifest": manifest}

    @staticmethod
    def digest(body: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
