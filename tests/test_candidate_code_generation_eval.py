from api.candidate_code_generation_eval import evaluate_candidate_code_generation


def test_candidate_code_generation_eval_blocks_lightweight_backend() -> None:
    result = evaluate_candidate_code_generation({"backend_kind": "lightweight-ngram"})

    assert result["ok"] is False
    assert "unsupported_code_generation_backend" in result["blockers"]


def test_candidate_code_generation_eval_requires_ready_transformers_backend() -> None:
    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"})

    assert result["ok"] is False
    assert "backend_ref_unsupported" in result["blockers"]


def test_candidate_code_generation_eval_runs_generated_code() -> None:
    def generator(case, _binding):
        if case["case_id"] == "python_add":
            return "def add(left, right):\n    return left + right\n"
        return "def reverse_string(value):\n    return value[::-1]\n"

    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"}, generator=generator)

    assert result["ok"] is True
    assert result["blockers"] == []
    assert result["passed_cases"] == result["total_cases"] == 2
    assert result["score"] == 1.0
    assert all(case["passed"] for case in result["cases"])


def test_candidate_code_generation_eval_fails_bad_generated_code() -> None:
    def generator(_case, _binding):
        return "def add(left, right):\n    return 0\n\ndef reverse_string(value):\n    return value\n"

    result = evaluate_candidate_code_generation({"backend_kind": "transformers-local"}, generator=generator)

    assert result["ok"] is False
    assert "benchmark_failed" in result["blockers"]
    assert result["score"] < 1.0
    assert any(not case["passed"] for case in result["cases"])
