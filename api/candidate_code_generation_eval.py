from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from api.runtime_ref import to_local_path

SCHEMA = "ailovanta.candidate_code_generation_eval.v1"
SUPPORTED_CODE_GENERATION_BACKENDS = {"transformers-local", "transformers-causal-lm"}
DEFAULT_MIN_SCORE = 1.0

CodeGenerator = Callable[[dict[str, Any], dict[str, Any]], str | dict[str, Any]]

DEFAULT_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "python_add",
        "language": "python",
        "prompt": (
            "Write a complete Python implementation for this function only:\n"
            "def add(left, right):\n"
            "    \"\"\"Return left + right.\"\"\"\n"
        ),
        "tests": (
            "from solution import add\n\n"
            "def test_add_numbers():\n"
            "    assert add(2, 3) == 5\n"
            "    assert add(-2, 7) == 5\n\n"
            "def test_add_strings():\n"
            "    assert add('ai', 'lovanta') == 'ailovanta'\n"
        ),
    },
    {
        "case_id": "python_reverse_string",
        "language": "python",
        "prompt": (
            "Write a complete Python implementation for this function only:\n"
            "def reverse_string(value):\n"
            "    \"\"\"Return value reversed.\"\"\"\n"
        ),
        "tests": (
            "from solution import reverse_string\n\n"
            "def test_reverse_string():\n"
            "    assert reverse_string('abc') == 'cba'\n"
            "    assert reverse_string('ailovanta') == 'atnavolia'\n"
            "    assert reverse_string('') == ''\n"
        ),
    },
)


def evaluate_candidate_code_generation(
    binding: dict[str, Any],
    *,
    cases: tuple[dict[str, Any], ...] | list[dict[str, Any]] | None = None,
    generator: CodeGenerator | None = None,
    min_score: float = DEFAULT_MIN_SCORE,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    backend_kind = str(binding.get("backend_kind") or "")
    if backend_kind not in SUPPORTED_CODE_GENERATION_BACKENDS:
        return _result(
            ok=False,
            blockers=["unsupported_code_generation_backend"],
            backend_kind=backend_kind,
            cases=[],
            score=0.0,
            reason="candidate backend cannot generate executable code for benchmark tasks",
        )

    selected_cases = tuple(cases or DEFAULT_CASES)
    if not selected_cases:
        return _result(
            ok=False,
            blockers=["no_code_generation_cases"],
            backend_kind=backend_kind,
            cases=[],
            score=0.0,
            reason="code generation benchmark has no cases",
        )

    resolved_generator = generator
    if resolved_generator is None:
        setup = _make_transformers_generator(binding)
        if not setup["ok"]:
            return _result(
                ok=False,
                blockers=[str(setup["blocker"])],
                backend_kind=backend_kind,
                cases=[],
                score=0.0,
                reason=str(setup["reason"]),
            )
        resolved_generator = setup["generator"]

    evaluated = [_evaluate_case(binding, case, resolved_generator, timeout_seconds) for case in selected_cases]
    passed = sum(1 for item in evaluated if item["passed"])
    score = passed / len(evaluated)
    blockers: list[str] = []
    if score < min_score:
        blockers.append("benchmark_failed")
    return _result(
        ok=not blockers,
        blockers=blockers,
        backend_kind=backend_kind,
        cases=evaluated,
        score=score,
        reason="code generation benchmark passed" if not blockers else "code generation benchmark failed",
        passed_cases=passed,
        total_cases=len(evaluated),
        min_score=min_score,
    )


def _evaluate_case(
    binding: dict[str, Any],
    case: dict[str, Any],
    generator: CodeGenerator,
    timeout_seconds: int,
) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "unknown")
    try:
        generated = generator(case, binding)
    except Exception as exc:
        return _case_result(case_id, False, reason="generation_exception", error=type(exc).__name__ + ": " + str(exc))

    if isinstance(generated, dict):
        if not generated.get("ok", True):
            return _case_result(
                case_id,
                False,
                reason=str(generated.get("reason") or "generation_failed"),
                error=str(generated.get("error") or ""),
            )
        code = str(generated.get("code") or "")
    else:
        code = str(generated or "")

    code = _extract_python_code(code)
    if not code.strip():
        return _case_result(case_id, False, reason="empty_generated_code")

    with tempfile.TemporaryDirectory(prefix="ailovanta-codegen-") as tmp:
        root = Path(tmp)
        (root / "solution.py").write_text(code, encoding="utf-8")
        tests_dir = root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_solution.py").write_text(str(case.get("tests") or ""), encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", str(tests_dir / "test_solution.py"), "-q"],
                cwd=str(root),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return _case_result(
                case_id,
                False,
                reason="pytest_timeout",
                stdout=_trim(exc.stdout or ""),
                stderr=_trim(exc.stderr or ""),
                code_sha256=hashlib.sha256(code.encode("utf-8")).hexdigest(),
            )
    passed = completed.returncode == 0
    return _case_result(
        case_id,
        passed,
        reason="passed" if passed else "pytest_failed",
        returncode=completed.returncode,
        stdout=_trim(completed.stdout),
        stderr=_trim(completed.stderr),
        code_sha256=hashlib.sha256(code.encode("utf-8")).hexdigest(),
    )


def _make_transformers_generator(binding: dict[str, Any]) -> dict[str, Any]:
    backend_ref = str(binding.get("backend_ref") or binding.get("checkpoint_uri") or "")
    model_path = to_local_path(backend_ref)
    if model_path is None:
        return {"ok": False, "blocker": "backend_ref_unsupported", "reason": "transformers backend_ref is not local"}
    if not model_path.exists():
        return {"ok": False, "blocker": "backend_ref_not_ready", "reason": "transformers model path is not reachable"}
    try:
        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except Exception:
        return {
            "ok": False,
            "blocker": "transformers_runtime_unavailable",
            "reason": "torch and transformers are required for executable code generation evaluation",
        }

    try:
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        model = AutoModelForCausalLM.from_pretrained(str(model_path))
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        model.eval()
    except Exception as exc:
        return {
            "ok": False,
            "blocker": "transformers_model_load_failed",
            "reason": "transformers model could not be loaded from backend_ref: " + type(exc).__name__,
        }

    def generate(case: dict[str, Any], _binding: dict[str, Any]) -> str:
        prompt = _benchmark_prompt(str(case.get("prompt") or ""))
        encoded = tokenizer(prompt, return_tensors="pt").to(device)
        output = model.generate(**encoded, max_new_tokens=192, do_sample=False)
        text = tokenizer.decode(output[0], skip_special_tokens=True)
        return text[len(prompt) :].strip() if text.startswith(prompt) else text.strip()

    return {"ok": True, "generator": generate}


def _benchmark_prompt(task_prompt: str) -> str:
    return (
        "You are writing benchmarked Python code. Return only valid Python code, no markdown.\n\n"
        + task_prompt.strip()
        + "\n"
    )


def _extract_python_code(text: str) -> str:
    fence = re.search(r"```(?:python|py)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text.strip()


def _case_result(case_id: str, passed: bool, **extra: Any) -> dict[str, Any]:
    return {"case_id": case_id, "passed": passed, **extra}


def _result(
    *,
    ok: bool,
    blockers: list[str],
    backend_kind: str,
    cases: list[dict[str, Any]],
    score: float,
    reason: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "ok": ok,
        "blockers": blockers,
        "backend_kind": backend_kind,
        "cases": cases,
        "score": score,
        "reason": reason,
        **extra,
    }


def _trim(value: str | bytes, limit: int = 1200) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"
