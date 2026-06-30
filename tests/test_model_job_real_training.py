import json
import urllib.error
from pathlib import Path

from api.model_job import resolve_dataset_path, run_model_job
from api.node_client import make_output, try_post
from api.training_artifact_binding import bind_local_training_artifact


def write_dataset(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                json.dumps({"text": "Ailovanta trains verified code intelligence."}),
                json.dumps({"text": "Workers produce artifacts from training data."}),
                json.dumps({"text": "Validation promotes only auditable candidates."}),
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_resolve_file_dataset_uri(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"

    assert resolve_dataset_path("file://" + str(dataset)) == dataset
    assert resolve_dataset_path(str(dataset)) == dataset
    assert resolve_dataset_path("https://example.test/train.jsonl") is None


def test_run_model_job_trains_lightweight_artifact(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "train.jsonl")
    output_dir = tmp_path / "model"

    result = run_model_job(
        {
            "name": "real-local",
            "version": "v1",
            "dataset_uri": "file://" + str(dataset),
            "base_model": "ailovanta-bootstrap",
            "max_steps": 3,
            "output_dir": str(output_dir),
        },
        {"cpu_threads": 4, "memory_gb": 16, "has_gpu": True},
        "job-real-1",
    )

    model = json.loads((output_dir / "ngram_model.json").read_text(encoding="utf-8"))
    record = json.loads((output_dir / "output.json").read_text(encoding="utf-8"))

    assert result["status"] == "candidate"
    assert result["metrics"]["backend"] == "lightweight-ngram"
    assert result["metrics"]["score"] > 0
    assert model["schema"] == "ailovanta.lightweight_ngram.v1"
    assert model["rows"] == 3
    assert model["train_loss"] > 0
    assert record["backend_message"].startswith("trained lightweight n-gram artifact")


def test_node_client_uses_model_job_training_backend(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "train.jsonl")
    output_dir = tmp_path / "node-model"

    result = make_output(
        {
            "id": "job-node-1",
            "type": "lora_micro",
            "payload": {
                "name": "node-real-local",
                "dataset_uri": "file://" + str(dataset),
                "base_model": "ailovanta-bootstrap",
                "max_steps": 2,
                "output_dir": str(output_dir),
            },
        },
        {"device_name": "test-node", "cpu_threads": 4, "memory_gb": 16, "has_gpu": True},
    )

    assert result["metrics"]["backend"] == "lightweight-ngram"
    assert (output_dir / "ngram_model.json").exists()


def test_bind_local_training_artifact_registers_runtime_binding(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "train.jsonl")
    output_dir = tmp_path / "node-model"
    result = run_model_job(
        {
            "name": "node-real-local",
            "dataset_uri": "file://" + str(dataset),
            "base_model": "ailovanta-bootstrap",
            "max_steps": 2,
            "output_dir": str(output_dir),
        },
        {"device_name": "test-node", "cpu_threads": 4, "memory_gb": 16, "has_gpu": True},
        "job-bind-1",
    )

    from api.artifact_binding import ArtifactBindingStore

    binding = bind_local_training_artifact(result, ArtifactBindingStore(tmp_path / "bindings.sqlite3"))

    assert binding is not None
    assert binding["model_key"] == "ailovanta-owned:candidate"
    assert binding["backend_kind"] == "lightweight-ngram"
    assert binding["status"] == "active"


def test_try_post_treats_missing_optional_catalog_as_none(monkeypatch) -> None:
    def missing(*_args, **_kwargs):
        raise urllib.error.HTTPError("http://test/catalog/items", 404, "not found", hdrs=None, fp=None)

    monkeypatch.setattr("api.node_client.post", missing)

    assert try_post("http://test", "/catalog/items", {"name": "x"}) is None
