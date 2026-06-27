from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_USES = {
    "inference",
    "rag",
    "finetune",
    "pretrain",
    "distillation",
    "evaluation",
    "benchmark",
    "commercial_runtime",
}

ACTIVE_STATUS = "active"
INACTIVE_STATUS = "inactive"
DEFAULT_RIGHTS_PATH = Path("runtime_data/rights_proofs.json")


class RightsProofError(ValueError):
    pass


class RightsProofRegistry:
    """Local Rights Proof Registry for Ailovanta-Code training."""

    def __init__(self, path: str | Path = DEFAULT_RIGHTS_PATH) -> None:
        self.path = Path(path)

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        return list(payload.get("rights") or [])

    def _write_all(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_rights(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        rights_id = str(item.get("rights_id") or "").strip()
        if not rights_id:
            raise RightsProofError("rights_id is required")

        allowed_uses = set(item.get("allowed_uses") or [])
        unknown_uses = allowed_uses - ALLOWED_USES
        if unknown_uses:
            raise RightsProofError(f"unknown allowed_uses: {sorted(unknown_uses)}")

        item.setdefault("status", ACTIVE_STATUS)
        item.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        item.setdefault("allowed_model_types", ["ailovanta-code"])
        item.setdefault("allowed_training_types", [])
        item.setdefault("commercial_use_allowed", False)
        item.setdefault("distillation_allowed", False)
        item.setdefault("redistribution_allowed", False)

        items = [existing for existing in self._read_all() if existing.get("rights_id") != rights_id]
        items.append(item)
        self._write_all(items)
        return item

    def get_rights(self, rights_id: str) -> dict[str, Any]:
        for item in self._read_all():
            if item.get("rights_id") == rights_id:
                return item
        raise RightsProofError(f"missing rights_id: {rights_id}")

    def list_rights(self, status: str | None = None) -> list[dict[str, Any]]:
        items = self._read_all()
        if status is None:
            return items
        return [item for item in items if item.get("status") == status]

    def deactivate_rights(self, rights_id: str, reason: str = "inactive") -> dict[str, Any]:
        items = self._read_all()
        for item in items:
            if item.get("rights_id") == rights_id:
                item["status"] = INACTIVE_STATUS
                item["status_reason"] = reason
                self._write_all(items)
                return item
        raise RightsProofError(f"missing rights_id: {rights_id}")

    def _is_expired(self, item: dict[str, Any]) -> bool:
        expires_at = item.get("expires_at")
        if not expires_at:
            return False
        normalized = str(expires_at).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized) <= datetime.now(timezone.utc)

    def can_train(self, rights_id: str, training_kind: str) -> bool:
        item = self.get_rights(rights_id)
        if item.get("status") != ACTIVE_STATUS:
            raise RightsProofError("rights status is not active")
        if self._is_expired(item):
            raise RightsProofError("rights are expired")

        allowed_training_types = set(item.get("allowed_training_types") or [])
        if training_kind not in allowed_training_types:
            raise RightsProofError(f"training kind not allowed: {training_kind}")

        if training_kind == "code_distill" and not bool(item.get("distillation_allowed")):
            raise RightsProofError("code_distill requires distillation_allowed=true")

        return True
