from pathlib import Path

from api.storage import SchedulerStore
from api.training_job_export import export_training_job


def test_export_training_job(tmp_path: Path) -> None:
    store = SchedulerStore(tmp_path / "scheduler.sqlite3")
    job = store.enqueue_job(
        "train_demo_001",
        "lora_micro",
        {
            "kind": "lora_micro",
            "name": "demo-job",
            "dataset_uri": "file://demo/docs",
            "base_model": "qwen2.5:3b",
            "max_steps": 120,
            "notes": "pytest export",
        },
    )

    result = export_training_job(job["id"], tmp_path / "exports", store=store)

    assert result["payload"]["schema_version"] == "ailovanta.training_job.v1"
    assert result["payload"]["job_id"] == job["id"]
    assert result["payload"]["kind"] == "lora_micro"
    assert Path(result["export_path"]).exists()
