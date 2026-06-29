from api.code_task_builder import task_from_instruction_record
from api.verified_code_samples import export_samples_from_reports, sample_from_task_run
from node_client.code_task_runner import run_code_instruction_task


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


def _passing_task() -> dict:
    return task_from_instruction_record(
        _record(),
        candidate_files={"app.py": "def add(left, right):\n    return left + right\n"},
        test_command=[["python", "-m", "pytest", "tests/test_app.py", "-q"]],
    )


def test_runner_attaches_verified_sample_for_passing_task() -> None:
    task = _passing_task()

    result = run_code_instruction_task(task)

    sample = result.report["verified_sample"]
    assert sample["schema_version"] == "ailovanta.verified_code_sample.v1"
    assert sample["instruction"] == "Implement add so the tests pass."
    assert sample["candidate_files"]["app.py"].startswith("def add")
    assert sample["verification"]["passed"] is True


def test_sample_from_task_run_skips_failed_report() -> None:
    task = _passing_task()
    report = {"passed": False, "report_hash": "sha256:bad"}

    assert sample_from_task_run(task, report) is None


def test_export_samples_from_reports_writes_only_passed_samples(tmp_path) -> None:
    task = _passing_task()
    passed = run_code_instruction_task(task).report
    failed = {"task": task, "report": {"passed": False, "report_hash": "sha256:bad"}}

    result = export_samples_from_reports([{"task": task, "report": passed}, failed], tmp_path / "samples.json")

    assert result["count"] == 1
    assert result["samples"][0]["sample_hash"].startswith("sha256:")
