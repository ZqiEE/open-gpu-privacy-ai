from pathlib import Path

from api.storage import SchedulerStore
from api.training_pipeline import run_training_pipeline


def test_training_pipeline_requires_core_path(tmp_path: Path) -> None:
    store = SchedulerStore(tmp_path / "scheduler.sqlite3")
    store.enqueue_job(
        "train_demo_001",
        "lora_micro",
        {
            "kind": "lora_micro",
            "name": "demo-job",
            "dataset_uri": "file://demo/docs",
            "base_model": "qwen2.5:3b",
        },
    )

    missing_core = tmp_path / "missing-core"
    try:
        run_training_pipeline("train_demo_001", core_path=missing_core, work_dir=tmp_path / "work", store=store)
    except ValueError as exc:
        assert "ailovanta-core path not found" in str(exc)
    else:
        raise AssertionError("missing core path should fail")


def test_training_pipeline_runs_core_bridge_and_registers_model(tmp_path: Path) -> None:
    store = SchedulerStore(tmp_path / "scheduler.sqlite3")
    store.enqueue_job(
        "train_demo_001",
        "lora_micro",
        {
            "kind": "lora_micro",
            "name": "demo-job",
            "dataset_uri": "file://demo/docs",
            "base_model": "qwen2.5:3b",
            "max_steps": 120,
        },
    )

    core_root = tmp_path / "ailovanta-core"
    scripts_dir = core_root / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "run_public_bridge.py").write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import json",
                "import sys",
                "from pathlib import Path",
                "",
                "input_path = Path(sys.argv[1])",
                "payload = json.loads(input_path.read_text(encoding='utf-8'))",
                "print(json.dumps({",
                "    'schema_version': 'ailovanta.core_result.v1',",
                "    'source_job_id': payload['job_id'],",
                "    'next_model_version': 'ailovanta-local-candidate',",
                "    'base_model': payload['base_model'],",
                "    'result_path': str(input_path.with_name('core_result.json')),",
                "}))",
            ]
        ),
        encoding="utf-8",
    )

    result = run_training_pipeline("train_demo_001", core_path=core_root, work_dir=tmp_path / "work", store=store)

    assert result["ok"] is True
    assert result["core_result"]["source_job_id"] == "train_demo_001"
    assert result["model_version"]["name"] == "ailovanta-local-candidate"
    assert result["model_version"]["source_job_id"] == "train_demo_001"
