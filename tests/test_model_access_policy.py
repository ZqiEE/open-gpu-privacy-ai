from __future__ import annotations

from api.model_access_policy import ModelAccessPolicy


def test_public_model_is_allowed() -> None:
    decision = ModelAccessPolicy().decide("public", {})
    assert decision.allowed is True


def test_confidential_model_requires_attested_node() -> None:
    node = {"reputation": 0.8, "stake": 5, "attested": True}
    decision = ModelAccessPolicy().decide("confidential", node)
    assert decision.allowed is True


def test_core_model_rejects_non_core_node() -> None:
    node = {"reputation": 1.0, "stake": 10, "attested": True, "core_node": False}
    decision = ModelAccessPolicy().decide("core", node)
    assert decision.allowed is False
