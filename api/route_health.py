from __future__ import annotations

from pathlib import Path
from typing import Any

from api.artifact_binding import ArtifactBindingStore
from api.artifact_integrity import verify_artifact_uri
from api.chain_registry import ChainRegistry
from api.chunk_manifest import manifest_hash
from api.owned_doctor import OwnedDoctor
from api.replica_book import status as replica_status
from api.route_book import RouteBook
from api.runtime_ref import to_local_path


ACTIVE_BINDING_STATUSES = {"active", "candidate"}


class RouteHealth:
    def __init__(
        self,
        routes: RouteBook | None = None,
        bindings: ArtifactBindingStore | None = None,
        doctor: OwnedDoctor | None = None,
        chain: ChainRegistry | None = None,
        replica_book_path: str | Path = "runtime_data/replica_book.json",
    ) -> None:
        self.routes = routes or RouteBook()
        self.bindings = bindings or ArtifactBindingStore()
        self.doctor = doctor or OwnedDoctor()
        self.chain = chain or ChainRegistry()
        self.replica_book_path = Path(replica_book_path)

    def check(self, route_key: str = "owned-chat/default", verify_artifact: bool = False, verify_distribution: bool = False, verify_chain: bool = False) -> dict[str, Any]:
        route = self.routes.get(route_key)
        blockers: list[str] = []
        if not route:
            return {"ok": False, "route_key": route_key, "route": None, "blockers": ["missing_route"]}
        if route.get("status") != "active":
            blockers.append("route_not_active")
        model_key = str(route.get("model_key") or "")
        if not model_key:
            blockers.append("missing_model_key")
        binding = self.bindings.latest_for_model(model_key) if model_key else None
        integrity = None
        distribution = None
        chain_anchor = None
        if not binding:
            blockers.append("missing_artifact_binding")
        elif binding.get("status") not in ACTIVE_BINDING_STATUSES:
            blockers.append("binding_not_active")
        else:
            if verify_artifact:
                uri = str(binding.get("checkpoint_uri") or binding.get("backend_ref") or "")
                expected = str(binding.get("artifact_hash") or "")
                integrity = verify_artifact_uri(uri, expected)
                if not integrity.get("ok"):
                    blockers.append("artifact_integrity:" + str(integrity.get("reason")))
            if verify_distribution:
                distribution = self.check_artifact_distribution(binding)
                if not distribution.get("ok"):
                    blockers.extend("artifact_distribution:" + str(item) for item in distribution.get("blockers", []))
            if verify_chain:
                chain_anchor = self.check_chain_anchor(binding)
                if not chain_anchor.get("ok"):
                    blockers.extend("chain_anchor:" + str(item) for item in chain_anchor.get("blockers", []))
        runtime = self.doctor.check(model_key) if model_key else {"ok": False, "blockers": ["missing_model_key"]}
        if not runtime.get("ok"):
            blockers.extend(str(item) for item in runtime.get("blockers", []) or ["runtime_not_ready"])
        return {
            "ok": not blockers,
            "route_key": route_key,
            "route": route,
            "model_key": model_key,
            "binding": binding,
            "artifact_integrity": integrity,
            "artifact_distribution": distribution,
            "chain_anchor": chain_anchor,
            "runtime": {"ok": runtime.get("ok"), "blockers": runtime.get("blockers")},
            "blockers": sorted(set(blockers)),
        }

    def check_artifact_distribution(self, binding: dict[str, Any]) -> dict[str, Any]:
        metadata = binding.get("metadata") if isinstance(binding.get("metadata"), dict) else {}
        distribution = metadata.get("artifact_distribution") if isinstance(metadata.get("artifact_distribution"), dict) else None
        blockers: list[str] = []
        if not distribution:
            return {"ok": False, "blockers": ["missing_artifact_distribution"]}

        storage_hash = str(distribution.get("storage_artifact_hash") or "")
        model_hash = str(distribution.get("model_artifact_hash") or binding.get("artifact_hash") or "")
        manifest_digest = str(distribution.get("manifest_hash") or "")
        manifest_uri = str(distribution.get("manifest_uri") or "")
        if not storage_hash:
            blockers.append("missing_storage_artifact_hash")
        if model_hash and model_hash != str(binding.get("artifact_hash") or ""):
            blockers.append("model_artifact_hash_mismatch")
        if not manifest_digest:
            blockers.append("missing_manifest_hash")
        manifest_check = self._check_manifest(manifest_uri, manifest_digest, storage_hash)
        if not manifest_check.get("ok"):
            blockers.extend("manifest:" + str(item) for item in manifest_check.get("blockers", []))

        book_path = Path(str(distribution.get("replica_book_path") or self.replica_book_path))
        book = replica_status(book_path)
        artifact_rows = [row for row in book.get("artifacts", []) if row.get("artifact_hash") == storage_hash]
        if not artifact_rows:
            blockers.append("missing_replica_book_artifact")
        elif not artifact_rows[0].get("healthy"):
            blockers.append("replica_book_under_replicated")
        return {
            "ok": not blockers,
            "blockers": sorted(set(blockers)),
            "distribution": {
                "artifact_id": distribution.get("artifact_id"),
                "model_artifact_hash": model_hash,
                "storage_artifact_hash": storage_hash,
                "manifest_hash": manifest_digest,
                "manifest_uri": manifest_uri,
            },
            "manifest": manifest_check,
            "replica_book_path": str(book_path),
            "replica_status": book,
            "replica_artifact": artifact_rows[0] if artifact_rows else None,
        }

    @staticmethod
    def _check_manifest(manifest_uri: str, expected_manifest_hash: str, expected_storage_hash: str) -> dict[str, Any]:
        blockers: list[str] = []
        if not manifest_uri:
            return {"ok": False, "blockers": ["missing_manifest_uri"]}
        path = to_local_path(manifest_uri)
        if path is None:
            return {"ok": False, "blockers": ["unsupported_manifest_uri"], "uri": manifest_uri}
        if not path.exists():
            return {"ok": False, "blockers": ["missing_manifest_file"], "uri": manifest_uri, "path": str(path)}
        try:
            import json

            manifest = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "blockers": ["invalid_manifest_json"], "uri": manifest_uri, "path": str(path), "error": exc.__class__.__name__}
        actual_manifest_hash = manifest_hash(manifest)
        if expected_manifest_hash and actual_manifest_hash != expected_manifest_hash:
            blockers.append("manifest_hash_mismatch")
        if expected_storage_hash and manifest.get("artifact_hash") != expected_storage_hash:
            blockers.append("manifest_artifact_hash_mismatch")
        return {
            "ok": not blockers,
            "blockers": sorted(set(blockers)),
            "uri": manifest_uri,
            "path": str(path),
            "artifact_hash": manifest.get("artifact_hash"),
            "manifest_hash": actual_manifest_hash,
            "chunk_count": len(manifest.get("chunks", []) or []),
        }

    def check_chain_anchor(self, binding: dict[str, Any]) -> dict[str, Any]:
        blockers: list[str] = []
        event = self.chain.latest_model_event(
            model_id=str(binding.get("model_id") or ""),
            version=str(binding.get("version") or ""),
            artifact_hash=str(binding.get("artifact_hash") or ""),
            runtime_manifest_hash=str(binding.get("runtime_manifest_hash") or ""),
        )
        if not event:
            return {"ok": False, "blockers": ["missing_chain_event"]}
        if not str(event.get("event_hash") or "").startswith("sha256:"):
            blockers.append("missing_event_hash")
        if event.get("anchor_status") != "anchored":
            blockers.append("event_not_anchored")
        if not str(event.get("chain_tx") or ""):
            blockers.append("missing_chain_tx")
        metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
        if metadata.get("binding_id") and metadata.get("binding_id") != binding.get("binding_id"):
            blockers.append("binding_id_mismatch")
        receipt = metadata.get("anchor_receipt") if isinstance(metadata.get("anchor_receipt"), dict) else None
        if not receipt:
            blockers.append("missing_anchor_receipt")
        else:
            payload = receipt.get("payload") if isinstance(receipt.get("payload"), dict) else {}
            if receipt.get("payload_hash") and receipt.get("payload_hash") not in {event.get("artifact_hash"), event.get("event_hash")}:
                blockers.append("anchor_payload_hash_mismatch")
            if payload.get("event_id") and payload.get("event_id") != event.get("event_id"):
                blockers.append("anchor_event_id_mismatch")
            if payload.get("event_hash") and payload.get("event_hash") != event.get("event_hash"):
                blockers.append("anchor_event_hash_mismatch")
        return {
            "ok": not blockers,
            "blockers": sorted(set(blockers)),
            "event": {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "event_hash": event.get("event_hash"),
                "anchor_status": event.get("anchor_status"),
                "chain_tx": event.get("chain_tx"),
                "artifact_hash": event.get("artifact_hash"),
                "runtime_manifest_hash": event.get("runtime_manifest_hash"),
            },
            "anchor_receipt": receipt,
        }

    def disable_if_bad(
        self,
        route_key: str = "owned-chat/default",
        reason: str = "route_health_failed",
        verify_artifact: bool = False,
        verify_distribution: bool = False,
        verify_chain: bool = False,
    ) -> dict[str, Any]:
        status = self.check(route_key, verify_artifact=verify_artifact, verify_distribution=verify_distribution, verify_chain=verify_chain)
        if status.get("ok"):
            return {"changed": False, "status": status}
        disabled = self.routes.disable(route_key, reason=reason + ":" + ",".join(status.get("blockers", []))) if status.get("route") else None
        return {"changed": bool(disabled), "status": status, "disabled": disabled}
