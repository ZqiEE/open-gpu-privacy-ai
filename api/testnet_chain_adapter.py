from __future__ import annotations

from typing import Any

from api.chain_adapter import ChainAdapter, ChainReceipt
from api.content_addressing import content_id, hash_object


class TestnetChainAdapter(ChainAdapter):
    """Dry-run adapter for future testnet integration.

    It never sends real transactions. It only returns deterministic references that
    the rest of the system can treat like chain receipts during development.
    """

    name = "testnet-dry-run"

    def __init__(self, network_name: str = "local-testnet") -> None:
        self.network_name = network_name
        self.submissions: list[dict[str, Any]] = []

    def submit_event(self, event: dict[str, Any]) -> ChainReceipt:
        payload_hash = hash_object(event)
        reference = content_id({"network": self.network_name, "event": payload_hash}, prefix="txdry")
        self.submissions.append({"kind": "event", "reference": reference, "payload_hash": payload_hash})
        return ChainReceipt(True, self.name, "submit_event", reference, payload_hash, "dry run only")

    def submit_model_commit(self, commit: dict[str, Any]) -> ChainReceipt:
        payload_hash = hash_object(commit)
        reference = content_id({"network": self.network_name, "commit": payload_hash}, prefix="txdry")
        self.submissions.append({"kind": "model_commit", "reference": reference, "payload_hash": payload_hash})
        return ChainReceipt(True, self.name, "submit_model_commit", reference, payload_hash, "dry run only")

    def status(self) -> dict[str, Any]:
        return {"adapter": self.name, "network": self.network_name, "dry_run_submissions": len(self.submissions)}
