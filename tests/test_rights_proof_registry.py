from __future__ import annotations

import pytest

from api.rights_proof_registry import RightsProofError, RightsProofRegistry


def sample_rights(**overrides):
    data = {
        "rights_id": "rights_demo",
        "provider_name": "Demo Provider",
        "provider_type": "investor",
        "agreement_id": "agr_demo",
        "agreement_uri": "file://agreement.pdf",
        "source_uri": "https://github.com/demo/repo",
        "source_type": "github_repo",
        "license_name": "MIT",
        "allowed_uses": ["finetune", "distillation", "evaluation", "commercial_runtime"],
        "allowed_model_types": ["ailovanta-code"],
        "allowed_training_types": ["code_lora", "code_qlora", "code_distill", "code_eval"],
        "commercial_use_allowed": True,
        "distillation_allowed": True,
        "redistribution_allowed": False,
        "expires_at": None,
        "status": "active",
    }
    data.update(overrides)
    return data


def test_active_rights_can_train(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    registry.add_rights(sample_rights())
    assert registry.can_train("rights_demo", "code_lora") is True


def test_inactive_rights_cannot_train(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    registry.add_rights(sample_rights())
    registry.deactivate_rights("rights_demo", "revoked")
    with pytest.raises(RightsProofError):
        registry.can_train("rights_demo", "code_lora")


def test_missing_rights_id_raises(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    with pytest.raises(RightsProofError):
        registry.can_train("missing", "code_lora")


def test_training_kind_must_be_allowed(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    registry.add_rights(sample_rights(allowed_training_types=["code_eval"]))
    with pytest.raises(RightsProofError):
        registry.can_train("rights_demo", "code_lora")


def test_distillation_requires_distillation_allowed(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    registry.add_rights(sample_rights(distillation_allowed=False))
    with pytest.raises(RightsProofError):
        registry.can_train("rights_demo", "code_distill")
