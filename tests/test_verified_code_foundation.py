from __future__ import annotations

from pathlib import Path

from api.verified_code_foundation import build_job_from_verified_code_export, export_to_dataset_shard


def verified_export() -> dict:
    return {
        "schema_version": "ailovanta.verified_code_sample_export.v1",
        "count": 1,
        "samples": [
            {
                "schema_version": "ailovanta.verified_code_sample.v1",
                "task_id": "task_1",
                "instruction": "Implement add(a, b).",
                "expected_response": "def add(a, b):\n    return a + b\n",
                "context_files": {"test_add.py": "from solution import add\nassert add(1, 2) == 3\n"},
                "candidate_files": {"solution.py": "def add(a, b):\n    return a + b\n"},
                "verification": {"passed": True, "report_hash": "sha256:report"},
                "sample_hash": "sha256:sample",
            }
        ],
    }


def test_verified_code_export_to_dataset_shard(tmp_path: Path) -> None:
    shard = export_to_dataset_shard(verified_export(), output_dir=tmp_path)
    assert shard["allowed_use"] == "verified_code_sft"
    assert shard["artifact_hash"].startswith("sha256:")
    assert Path(shard["dataset_path"]).exists()


def test_build_job_from_verified_code_export(tmp_path: Path) -> None:
    job = build_job_from_verified_code_export(verified_export(), dataset_output_dir=tmp_path, max_steps=7)
    assert job["schema_version"] == "ailovanta.foundation_job.v1"
    assert job["stage"] == "verified_code_sft"
    assert job["execute_checkpoints"] is True
    assert job["max_steps"] == 7
    assert job["metadata"]["row_count"] == 1
