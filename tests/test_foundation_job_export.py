from pathlib import Path

from api.foundation_job_export import export_foundation_job
from api.foundation_job_store import FoundationJobStore


def test_export_foundation_job(tmp_path: Path) -> None:
    store = FoundationJobStore(tmp_path / "foundation_jobs.sqlite3")
    job = store.create(
        {
            "model": {"model_id": "ailovanta-owned", "target_version": "candidate"},
            "dataset_shards": [
                {"shard_id": "shard_1", "source_id": "src_1", "uri": "file://data", "token_count": 100000}
            ],
            "nodes": [{"node_id": "gpu_1", "gpu_memory_gb": 24}],
            "stage": "pretrain",
            "max_steps": 100,
        }
    )

    result = export_foundation_job(job["job_id"], tmp_path / "exports", store=store)

    assert result["payload"]["schema_version"] == "ailovanta.foundation_job.v1"
    assert result["payload"]["job_id"] == job["job_id"]
    assert Path(result["export_path"]).exists()
