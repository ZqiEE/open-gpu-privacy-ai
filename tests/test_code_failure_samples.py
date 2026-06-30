from __future__ import annotations

import json

from api.code_failure_samples import export_failures_from_reports, failure_from_task_run
from api.code_task_builder import task_from_instruction_record
from node_client.code_task_runner import run_code_instruction_task


def _task() -> dict:
    record = {
        "training_record_kind": "instruction",
        "path": "tests/test_app.py",
        "record_type": "test_spec",
        "language": "python",
        "sha256": "sha256:test",
        "instruction": "Implement add so the tests pass.",
        "context": "from app import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        "expected_response": "Create an add function that returns the sum.",
    }
    return task_from_instruction_record(
        record,
        candidate_files={"app.py": "def add(left, right):\n    return left - right\n"},
        test_command=[["python", "-m", "pytest", "tests/test_app.py", "-q"]],
    )


def test_failure_sample_contains_repair_prompt() -> None:
    task = _task()
    report = run_code_instruction_task(task).report

    sample = failure_from_task_run(task, report)

    assert sample is not None
    assert sample["schema_version"] == "ailovanta.failed_code_sample.v1"
    assert sample["training_use"]["positive_sft"] is False
    assert sample["training_use"]["repair_task"] is True
    assert "Repair the candidate code" in sample["repair_prompt"]
    assert sample["sample_hash"].startswith("sha256:")


def test_export_failures_from_reports_writes_only_failed(tmp_path) -> None:
    task = _task()
    failed_report = run_code_instruction_task(task).report
    passed_report = {**failed_report, "passed": True}

    result = export_failures_from_reports(
        [{"task": task, "report": failed_report}, {"task": task, "report": passed_report}],
        tmp_path / "failures.json",
    )

    assert result["count"] == 1
    payload = json.loads((tmp_path / "failures.json").read_text(encoding="utf-8"))
    assert payload["samples"][0]["failure"]["report_hash"]
