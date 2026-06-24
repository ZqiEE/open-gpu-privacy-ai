from pathlib import Path

from api.core_result_store import CoreResultStore
from api.runtime_store import RuntimeStore


def test_register_core_result_and_runtime_model(tmp_path: Path) -> None:
    core_results = CoreResultStore(tmp_path / "core_results.sqlite3")
    runtime_store = RuntimeStore(tmp_path / "runtime.sqlite3")

    result = core_results.register_manifest(
        {
            "schema_version": "ailovanta.core_result.v1",
            "source_job_id": "train_demo",
            "round_id": "round_demo",
            "accepted_candidates": 1,
            "next_model_version": "ailovanta-local-v1",
            "base_model": "ailovanta-bootstrap:local",
            "dataset_uri": "file://demo/docs",
            "promotion_status": "candidate",
        }
    )

    registered = core_results.promote_to_runtime(result["result_id"], runtime_store)

    assert registered["ok"] is True
    assert registered["runtime_model"]["model_id"] == "ailovanta-owned"
    assert registered["runtime_model"]["version"] == "ailovanta-local-v1"
    assert registered["runtime_model"]["privacy_level"] == "protected"
    assert "trusted_runtime_pool" in registered["runtime_model"]["allowed_pools"]
    assert registered["runtime_model"]["manifest_hash"].startswith("sha256:")
