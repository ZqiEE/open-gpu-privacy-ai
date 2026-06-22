from __future__ import annotations

from node_client.task_policy import TaskPolicy


def test_policy_accepts_allowed_job() -> None:
    policy = TaskPolicy.default()
    ok, reason = policy.validate({"id": "j1", "type": "evaluation", "payload": {"samples": 3}})
    assert ok is True
    assert reason == "accepted"


def test_policy_rejects_unknown_job_type() -> None:
    policy = TaskPolicy.default()
    ok, reason = policy.validate({"id": "j2", "type": "unknown_job", "payload": {}})
    assert ok is False
    assert "not allowed" in reason


def test_policy_rejects_large_payload() -> None:
    policy = TaskPolicy(allowed_job_types={"evaluation"}, max_payload_bytes=16)
    ok, reason = policy.validate({"id": "j3", "type": "evaluation", "payload": {"text": "x" * 200}})
    assert ok is False
    assert "payload too large" in reason
