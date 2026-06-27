from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.artifact_integrity import verify_catalog_item
from api.catalog import Catalog
from api.prod_config import load_config
from api.receipt_gate import ready_for_catalog_publish


def check_chunk_manifest_ref(ref: Any) -> dict[str, Any]:
    blockers: list[str] = []
    if not isinstance(ref, dict):
        return {"ok": False, "blockers": ["missing_artifact_manifest"]}
    uri = str(ref.get("uri") or ref.get("manifest_uri") or "")
    if not uri:
        blockers.append("artifact_manifest_missing_uri")
    if int(ref.get("chunk_count") or 0) <= 0:
        blockers.append("artifact_manifest_missing_chunks")
    if int(ref.get("chunk_size") or 0) <= 0:
        blockers.append("artifact_manifest_missing_chunk_size")
    return {"ok": not blockers, "blockers": blockers, "uri": uri, "chunk_count": ref.get("chunk_count"), "chunk_size": ref.get("chunk_size")}


def check_chunk_manifest_file(uri: str) -> dict[str, Any]:
    if not uri.startswith("file://"):
        return {"ok": True, "skipped": True, "reason": "non_file_manifest_uri"}
    path = Path(uri.removeprefix("file://"))
    if not path.exists():
        return {"ok": False, "blockers": ["artifact_manifest_file_missing"], "path": str(path)}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "blockers": ["artifact_manifest_json_error:" + exc.__class__.__name__], "path": str(path)}
    blockers: list[str] = []
    chunks = manifest.get("chunks") if isinstance(manifest.get("chunks"), list) else []
    if not chunks:
        blockers.append("artifact_manifest_no_chunks")
    for chunk in chunks:
        if not str(chunk.get("chunk_hash") or "").startswith("sha256:"):
            blockers.append("chunk_missing_sha256")
        sources = chunk.get("sources") if isinstance(chunk.get("sources"), list) else []
        if not sources:
            blockers.append("chunk_missing_sources")
    return {"ok": not blockers, "blockers": sorted(set(blockers)), "path": str(path), "chunk_count": len(chunks)}


class ReadinessAudit:
    def __init__(self, catalog: Catalog | None = None) -> None:
        self.catalog = catalog or Catalog()

    def check_item(self, item: dict[str, Any], verify_bytes: bool = False) -> dict[str, Any]:
        gate = ready_for_catalog_publish(item)
        blockers: list[str] = []
        warnings: list[str] = []
        uri = str(item.get("artifact_uri") or item.get("location") or "")
        digest = str(item.get("artifact_hash") or item.get("digest") or "")
        if not uri:
            blockers.append("missing_artifact_uri")
        if uri and not uri.startswith(("s3://", "ipfs://", "file://", "http://", "https://")):
            blockers.append("artifact_uri_not_portable")
        if uri.startswith("file://"):
            warnings.append("local_file_artifact")
        if not digest.startswith("sha256:"):
            blockers.append("artifact_hash_not_sha256")
        if not gate.get("ok"):
            blockers.append("publish_gate:" + str(gate.get("reason")))
        manifest_ref = check_chunk_manifest_ref(item.get("artifact_manifest"))
        if not manifest_ref.get("ok"):
            blockers.extend(str(item) for item in manifest_ref.get("blockers", []))
        manifest_file = check_chunk_manifest_file(str(manifest_ref.get("uri") or "")) if manifest_ref.get("uri") else None
        if manifest_file and not manifest_file.get("ok"):
            blockers.extend(str(item) for item in manifest_file.get("blockers", []))
        integrity = None
        if verify_bytes and uri and digest.startswith("sha256:"):
            try:
                integrity = verify_catalog_item(item)
                if not integrity.get("ok"):
                    blockers.append("artifact_integrity:" + str(integrity.get("reason")))
            except Exception as exc:
                integrity = {"ok": False, "reason": exc.__class__.__name__}
                blockers.append("artifact_integrity_error:" + exc.__class__.__name__)
        return {"item_id": item.get("id"), "name": item.get("name"), "version": item.get("version"), "status": item.get("status"), "ok": not blockers, "blockers": sorted(set(blockers)), "warnings": warnings, "gate": gate, "integrity": integrity, "artifact_manifest": {"ref": manifest_ref, "file": manifest_file}, "artifact_uri": uri, "artifact_hash": digest}

    def check_catalog(self, status: str | None = "published", verify_bytes: bool = False) -> dict[str, Any]:
        items = self.catalog.list(status=status)
        checked = [self.check_item(item, verify_bytes=verify_bytes) for item in items]
        blockers = [item for item in checked if not item["ok"]]
        return {"ok": not blockers, "status": status, "verify_bytes": verify_bytes, "count": len(checked), "blockers": blockers, "items": checked}

    def check_manifests(self, manifest_dir: str | Path = "runtime_data/manifests") -> dict[str, Any]:
        root = Path(manifest_dir)
        if not root.exists():
            return {"ok": True, "count": 0, "items": []}
        checked: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        for path in sorted(root.glob("*.json")):
            item_blockers: list[str] = []
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                manifest = {}
                item_blockers.append("manifest_json_error:" + exc.__class__.__name__)
            digest = str(manifest.get("artifact_hash") or manifest.get("digest") or "")
            if manifest and not digest.startswith("sha256:"):
                item_blockers.append("manifest_missing_sha256_hash")
            if manifest and not manifest.get("proof"):
                item_blockers.append("manifest_missing_proof")
            if manifest:
                ref = check_chunk_manifest_ref(manifest.get("artifact_manifest"))
                if not ref.get("ok"):
                    item_blockers.extend(str(item) for item in ref.get("blockers", []))
            route = manifest.get("route") if isinstance(manifest.get("route"), dict) else {}
            if manifest and not manifest.get("anchor_receipt") and not route.get("receipt"):
                item_blockers.append("manifest_missing_anchor_receipt")
            item = {"path": str(path), "ok": not item_blockers, "blockers": sorted(set(item_blockers)), "name": manifest.get("name"), "version": manifest.get("version")}
            checked.append(item)
            if item_blockers:
                blockers.append(item)
        return {"ok": not blockers, "count": len(checked), "blockers": blockers, "items": checked}

    def production_check(self, verify_bytes: bool = False) -> dict[str, Any]:
        cfg = load_config()
        blockers: list[str] = []
        warnings: list[str] = []
        if cfg.env != "local" and cfg.artifact_store == "local":
            blockers.append("production_artifact_store_is_local")
        if cfg.env != "local" and cfg.chain_anchor == "file":
            blockers.append("production_anchor_is_file")
        if cfg.env == "local":
            warnings.append("local_environment")
        catalog = self.check_catalog(status="published", verify_bytes=verify_bytes)
        manifests = self.check_manifests()
        if not catalog.get("ok"):
            blockers.append("catalog_readiness_failed")
        if not manifests.get("ok"):
            blockers.append("manifest_readiness_failed")
        return {"ok": not blockers, "blockers": blockers, "warnings": warnings, "verify_bytes": verify_bytes, "catalog": catalog, "manifests": manifests}
