import json
from pathlib import Path

from api.code_task_builder import build_tasks_from_corpus, task_from_instruction_record
from node_client.code_task_runner import run_code_instruction_task
from node_client.job_runner import JobRunner


def _record() -> dict:
    return {
        "training_record_kind": "instruction",
        "path": "tests/test_app.py",
        "record_type": "test_spec",
        "language": "python",
        "sha256": "sha256:test",
        "instruction": "Implement add so the tests pass.",
        "context": "from app import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        "expected_response": "Create an add function that returns the sum.",
    }


def test_task_builder_writes_executable_task_file(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(json.dumps(_record(), ensure_ascii=False) + "\n", encoding="utf-8")

    result = build_tasks_from_corpus(corpus, tmp_path / "tasks.json")

    assert result["tasks"] == 1
    payload = json.loads((tmp_path / "tasks.json").read_text(encoding="utf-8"))
    task = payload["tasks"][0]
    assert task["type"] == "code_instruction_eval"
    assert task["payload"]["files"]["tests/test_app.py"].startswith("from app import add")


def test_code_instruction_runner_passes_verified_python_task() -> None:
    task = task_from_instruction_record(
        _record(),
        candidate_files={"app.py": "def add(left, right):\n    return left + right\n"},
        test_command=[["python", "-m", "pytest", "tests/test_app.py", "-q"]],
    )

    result = run_code_instruction_task(task)

    assert result.passed is True
    assert result.report["commands"][0]["returncode"] == 0


def test_code_instruction_runner_blocks_unapproved_command() -> None:
    task = task_from_instruction_record(_record(), test_command=[["cmd", "/c", "echo unsafe"]])

    result = run_code_instruction_task(task)

    assert result.passed is False
    assert result.report["commands"][0]["reason"] == "command_not_allowed"


def test_job_runner_executes_code_instruction_eval() -> None:
    task = task_from_instruction_record(
        _record(),
        candidate_files={"app.py": "def add(left, right):\n    return left + right\n"},
        test_command=[["python", "-m", "pytest", "tests/test_app.py", "-q"]],
    )

    result = JobRunner().run(task)

    assert result.status == "ok"
    report = json.loads(result.output_summary)
    assert report["passed"] is True
