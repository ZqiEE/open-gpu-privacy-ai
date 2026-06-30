from api.compat_check import check_real_training_requirements, classify_base_model_ref, training_backend_from_payload


def test_real_training_preflight_reports_gpu_and_missing_base_path() -> None:
    result = check_real_training_requirements(
        {
            "real": True,
            "use_transformers": True,
            "peft": True,
            "lora": True,
            "requires_gpu": True,
            "base_model": "Z:/missing/ailovanta-model",
        },
        {"has_gpu": False},
    )

    assert result["ok"] is False
    assert result["backend"] == "lora"
    assert "gpu_required_but_node_has_no_gpu" in result["blockers"]
    assert "base_model_path_missing" in result["blockers"]


def test_real_training_preflight_classifies_qlora() -> None:
    assert training_backend_from_payload({"qlora": True, "peft": True}) == "qlora"
    assert classify_base_model_ref("sshleifer/tiny-gpt2")["kind"] == "hf_or_remote"
