from __future__ import annotations

from node_client.job_descriptor import JobDescriptorPolicy


def test_descriptor_optional_when_not_required() -> None:
    policy = JobDescriptorPolicy(required=False)
    result = policy.validate({"id": "j1", "type": "evaluation", "payload": {}})
    assert result.ok is True


def test_descriptor_required_can_reject_missing() -> None:
    policy = JobDescriptorPolicy(required=True)
    result = policy.validate({"id": "j2", "type": "evaluation", "payload": {}})
    assert result.ok is False
    assert result.reason == "missing descriptor"
