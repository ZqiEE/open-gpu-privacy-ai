from __future__ import annotations

import json
import sys

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


def test_repair_loop_accepts_external_candidate_command(tmp_path) -> None:
    task = _failing_task()
    failed_report = run_code_instruction_task(task).report
    generator = tmp_path / "generator.py"
    generator.write_text(
        "\n".join(
            [
                "import argparse, json",
                "p = argparse.ArgumentParser()",
                "p.add_argument('--input')",
                "p.add_argument('--output')",
                "p.add_argument('--max-candidates')",
                "args = p.parse_args()",
                "payload = {",
                "  'schema_version': 'ailovanta.core.code_repair_candidates.v1',",
                "  'count': 1,",
                "  'candidates': [{'candidate_id': 'core_demo', 'strategy': 'core:test_candidate', 'files': {'app.py': 'def add(left, right):\\n    return left + right\\n'}}],",
                "}",
                "open(args.output, 'w', encoding='utf-8').write(json.dumps(payload))",
            ]
        ),
        encoding="utf-8",
    )

    result = repair_failed_task(
        task,
        failed_report,
        max_candidates=1,
        candidate_command=f"{sys.executable} {generator}",
    )

    assert result["verified_report_items"]
    assert result["attempts"][0]["strategy"] == "core:test_candidate"


def test_repair_loop_passes_backend_ref_to_external_candidate_command(tmp_path) -> None:
    task = _failing_task()
    failed_report = run_code_instruction_task(task).report
    marker = tmp_path / "seen_backend_ref.txt"
    generator = tmp_path / "generator.py"
    generator.write_text(
        "\n".join(
            [
                "import argparse, json",
                "p = argparse.ArgumentParser()",
                "p.add_argument('--input')",
                "p.add_argument('--output')",
                "p.add_argument('--max-candidates')",
                "p.add_argument('--backend-ref')",
                "args = p.parse_args()",
                f"open({str(marker)!r}, 'w', encoding='utf-8').write(args.backend_ref or '')",
                "payload = {'schema_version': 'ailovanta.core.code_repair_candidates.v1', 'count': 1, 'candidates': [{'candidate_id': 'core_demo', 'strategy': 'core:backend_candidate', 'files': {'app.py': 'def add(left, right):\\n    return left + right\\n'}}]}",
                "open(args.output, 'w', encoding='utf-8').write(json.dumps(payload))",
            ]
        ),
        encoding="utf-8",
    )

    result = repair_failed_task(
        task,
        failed_report,
        max_candidates=1,
        candidate_command=f"{sys.executable} {generator}",
        backend_ref="file:///tmp/checkpoint.bin",
    )

    assert result["verified_report_items"]
    assert marker.read_text(encoding="utf-8") == "file:///tmp/checkpoint.bin"
