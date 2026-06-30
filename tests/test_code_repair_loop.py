from __future__ import annotations

import json

from api.code_repair_loop import repair_failed_task, repair_failures_from_reports
from api.code_task_builder import task_from_instruction_record
from node_client.code_task_runner import run_code_instruction_task


def _failing_task() -> dict:
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


def test_repair_failed_task_verifies_mutated_candidate() -> None:
    task = _failing_task()
    failed_report = run_code_instruction_task(task).report

    result = repair_failed_task(task, failed_report, max_candidates=8)

    assert result["verified_report_items"]
    assert result["attempts"][-1]["passed"] is True
    assert result["preference_pairs"][0]["training_use"]["preference"] is True
    repaired = result["verified_report_items"][0]["task"]["payload"]["files"]["app.py"]
    assert "return left + right" in repaired


def test_repair_failures_from_reports_writes_export(tmp_path) -> None:
    task = _failing_task()
    failed_report = run_code_instruction_task(task).report

    result = repair_failures_from_reports([{"task": task, "report": failed_report}], tmp_path / "repairs.json")

    assert result["repaired"] == 1
    payload = json.loads((tmp_path / "repairs.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "ailovanta.code_repair_export.v1"
    assert payload["preference_pairs"][0]["reward"]["chosen_test_passed"] is True
