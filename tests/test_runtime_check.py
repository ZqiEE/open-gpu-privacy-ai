from __future__ import annotations

from api.runtime_check import RuntimeCheckPolicy


def test_runtime_check_accepts_matching_quote() -> None:
    policy = RuntimeCheckPolicy(allowed_runtime_hashes={"runtime_a"})
    report = policy.verify("node_a", "runtime_a", "simulated-safe-box", {"node_id": "node_a"})
    assert report["passed"] is True


def test_runtime_check_rejects_node_mismatch() -> None:
    report = RuntimeCheckPolicy().verify("node_a", "runtime_a", "simulated-safe-box", {"node_id": "node_b"})
    assert report["passed"] is False
