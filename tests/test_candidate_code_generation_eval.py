from api.candidate_code_generation_eval import evaluate_candidate_code_generation


def test_candidate_code_generation_eval_blocks_lightweight_backend() -> None:
    result = evaluate_candidate_code_generation({"backend_kind": "lightweight-ngram"})

    assert result["ok"] is False
    assert "unsupported_code_generation_backend" in result["blockers"]


def test_candidate_code_generation_eval_requires_configured_runner_for_transformers() -> None:
    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"})

    assert result["ok"] is False
    assert "code_generation_eval_not_configured" in result["blockers"]
