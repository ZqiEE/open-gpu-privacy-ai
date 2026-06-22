from __future__ import annotations

from api.decentralized_identity import create_ledger_identity, identity_hash


def test_create_ledger_identity_is_hashable() -> None:
    identity = create_ledger_identity("node_test", "pytest-node")
    assert identity["node_id"] == "node_test"
    assert identity["ledger_address"].startswith("addr_")
    assert identity_hash(identity)
