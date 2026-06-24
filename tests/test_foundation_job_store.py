from pathlib import Path

from api.foundation_job_store import FoundationJobStore


def test_create_foundation_job(tmp_path: Path) -> None:
    store = FoundationJobStore(tmp_path / "foundation_jobs.sqlite3")
    job = store.create(
        {
            "model": {"model_id": "ailovanta-owned", "target_version": "candidate", "parameter_count_b": 1.0},
            "dataset_shards": [
                {"shard_id": "shard_1", "source_id": "src_1", "uri": "file://data", "token_count": 100000}
            ],
            "nodes": [{"node_id": "gpu_1", "gpu_memory_gb": 24}],
            "stage": "pretrain",
            "max_steps": 100,
        }
    )

    assert job["model_id"] == "ailovanta-owned"
    assert job["target_version"] == "candidate"
    assert job["payload"]["schema_version"] == "ailovanta.foundation_job.v1"
    assert store.get(job["job_id"])["job_id"] == job["job_id"]
