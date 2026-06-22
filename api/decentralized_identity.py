from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time

from api.content_addressing import content_id, hash_object


@dataclass(frozen=True)
class LedgerIdentity:
    node_id: str
    ledger_address: str
    public_label: str
    created_at: float


def create_ledger_identity(node_id: str, public_label: str = "ai-node") -> dict:
    payload = {"node_id": node_id, "public_label": public_label}
    identity = LedgerIdentity(
        node_id=node_id,
        ledger_address=content_id(payload, prefix="addr"),
        public_label=public_label,
        created_at=round(time(), 3),
    )
    return asdict(identity)


def identity_hash(identity: dict) -> str:
    return hash_object({"node_id": identity["node_id"], "ledger_address": identity["ledger_address"]})
