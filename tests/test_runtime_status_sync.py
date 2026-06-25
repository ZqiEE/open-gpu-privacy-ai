from api.runtime_router import ModelManifest
from api.runtime_status_sync import sync_model_with_ref_check
from api.runtime_store import RuntimeStore


def test_sync_model_unavailable_when_ref_not_ready(tmp_path) -> None:
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    runtime.register_model(
        ModelManifest(
            model_id="ailovanta-owned",
            version="candidate",
            manifest_hash="sha256:r",
            privacy_level="protected",
            min_gpu_memory_gb=0,
            allowed_pools=["trusted_runtime_pool"],
            quantization="candidate",
            context_length=8192,
            adapter_compatible=True,
            status="active",
        )
    )
    update = sync_model_with_ref_check(runtime, "ailovanta-owned:candidate", False)
    assert update["after"] == "unavailable"
    assert runtime.get_model("ailovanta-owned:candidate")["status"] == "unavailable"


def test_sync_model_candidate_when_ref_ready_again(tmp_path) -> None:
    runtime = RuntimeStore(tmp_path / "runtime.sqlite3")
    runtime.register_model(
        ModelManifest(
            model_id="ailovanta-owned",
            version="candidate",
            manifest_hash="sha256:r",
            privacy_level="protected",
            min_gpu_memory_gb=0,
            allowed_pools=["trusted_runtime_pool"],
            quantization="candidate",
            context_length=8192,
            adapter_compatible=True,
            status="unavailable",
        )
    )
    update = sync_model_with_ref_check(runtime, "ailovanta-owned:candidate", True)
    assert update["after"] == "candidate"
