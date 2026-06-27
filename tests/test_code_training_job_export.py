from __future__ import annotations

import pytest

from api.code_training_jobs import CodeTrainingJobError, CodeTrainingJobStore
from api.rights_proof_registry import RightsProofError, RightsProofRegistry


def add_rights(registry: RightsProofRegistry, status: str = "active") -> None:
    registry.add_rights(
        {
            "rights_id": "rights_code",
            "provider_name": "Demo Provider",
            "provider_type": "partner",
            "agreement_id": "agr_code",
            "agreement_uri": "file://agreement.pdf",
            "source_uri": "https://github.com/demo/code",
            "source_type": "github_repo",
            "license_name": "Apache-2.0",
            "allowed_uses": ["finetune", "distillation", "evaluation"],
            "allowed_model_types": ["ailovanta-code"],
            "allowed_training_types": ["code_lora", "code_qlora", "code_distill", "code_eval"],
            "commercial_use_allowed": True,
            "distillation_allowed": True,
            "redistribution_allowed": False,
            "expires_at": None,
            "status": status,
        }
    )


def test_code_lora_job_is_distributed(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    add_rights(registry)
    store = CodeTrainingJobStore(tmp_path / "jobs.json", rights_registry=registry)

    job = store.create_job(rights_id="rights_code", dataset_id="dataset_code", kind="code_lora")

    assert job["schema_version"] == "ailovanta.training_job.v1"
    assert job["kind"] == "code_lora"
    assert job["rights_id"] == "rights_code"
    assert job["distributed_required"] is True
    assert job["target_model"] == "ailovanta-code"


def test_inactive_rights_cannot_create_job(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    add_rights(registry, status="inactive")
    store = CodeTrainingJobStore(tmp_path / "jobs.json", rights_registry=registry)

    with pytest.raises(RightsProofError):
        store.create_job(rights_id="rights_code", dataset_id="dataset_code", kind="code_lora")


def test_unsupported_kind_raises(tmp_path):
    registry = RightsProofRegistry(tmp_path / "rights.json")
    add_rights(registry)
    store = CodeTrainingJobStore(tmp_path / "jobs.json", rights_registry=registry)

    with pytest.raises(CodeTrainingJobError):
        store.create_job(rights_id="rights_code", dataset_id="dataset_code", kind="single_machine_train")
