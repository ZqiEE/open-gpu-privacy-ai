import json
import urllib.error
from pathlib import Path

from api.model_job import resolve_dataset_path, run_model_job
from api.node_client import make_output, submit_failure_actions, try_post
from api.training_artifact_binding import bind_local_training_artifact


def write_dataset(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                json.dumps({"text": "def add(left, right):\n    return left + right\n", "record_kind": "code", "source_path": "app.py"}),
                json.dumps({"text": "def reverse_string(value):\n    return value[::-1]\n", "record_kind": "code", "source_path": "strings.py"}),
                json.dumps({"text": "Instruction: implement tested Python functions.\nExpected: code should compile.", "record_kind": "instruction", "source_path": "README.md"}),
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_plain_dataset(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                json.dumps({"text": "Ailovanta trains verified intelligence."}),
                json.dumps({"text": "Workers produce artifacts from training data."}),
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


def test_bind_local_training_artifact_keeps_lightweight_backend_candidate_until_code_generation_eval(tmp_path: Path) -> None:
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

    binding = bind_local_training_artifact(
        result,
        ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        manifest_dir=tmp_path / "artifact_manifests",
        replica_book_path=tmp_path / "replica_book.json",
        replica_tasks_path=tmp_path / "replica_repair_tasks.json",
        replica_storage_root=tmp_path / "storage_replicas",
    )

    assert binding is not None
    assert binding["model_key"] == "ailovanta-owned:candidate"
    assert binding["backend_kind"] == "lightweight-ngram"
    assert binding["status"] == "candidate"
    distribution = binding["metadata"]["artifact_distribution"]
    assert distribution["schema_version"] == "ailovanta.artifact_distribution.v1"
    assert distribution["manifest_hash"].startswith("sha256:")
    assert Path(distribution["manifest_uri"].removeprefix("file://")).exists()
    assert distribution["replica_book_path"].endswith("replica_book.json")
    assert binding["metadata"]["storage_policy"]["mode"] == "distributed_chunk_manifest"
    gate = binding["metadata"]["promotion_gate"]
    assert gate["ok"] is False
    assert gate["decision"] == "keep_candidate"
    assert gate["code_eval"]["ok"] is True
    assert gate["code_eval"]["syntax_checks"] >= 1
    assert gate["code_generation_eval"]["ok"] is False
    assert "code_generation:unsupported_code_generation_backend" in gate["blockers"]
    assert binding["metadata"]["failure_actions"]["actions"][0]["action_type"] == "training_retrain"


def test_bind_local_training_artifact_keeps_under_replicated_artifact_candidate(tmp_path: Path) -> None:
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
        "job-bind-candidate",
    )

    from api.artifact_binding import ArtifactBindingStore

    binding = bind_local_training_artifact(
        result,
        ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        manifest_dir=tmp_path / "artifact_manifests",
        replica_book_path=tmp_path / "replica_book.json",
        auto_repair_replicas=False,
    )

    assert binding is not None
    assert binding["status"] == "candidate"
    assert binding["metadata"]["promotion_gate"]["ok"] is False
    assert "artifact_distribution:replica_book_under_replicated" in binding["metadata"]["promotion_gate"]["blockers"]
    assert binding["metadata"]["failure_actions"]["actions"][0]["action_type"] == "training_retrain"


def test_bind_local_training_artifact_requires_code_eval(tmp_path: Path) -> None:
    dataset = write_plain_dataset(tmp_path / "plain.jsonl")
    output_dir = tmp_path / "node-model"
    result = run_model_job(
        {
            "name": "node-plain-local",
            "dataset_uri": "file://" + str(dataset),
            "base_model": "ailovanta-bootstrap",
            "max_steps": 2,
            "output_dir": str(output_dir),
        },
        {"device_name": "test-node", "cpu_threads": 4, "memory_gb": 16, "has_gpu": True},
        "job-bind-plain",
    )

    from api.artifact_binding import ArtifactBindingStore

    binding = bind_local_training_artifact(
        result,
        ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        manifest_dir=tmp_path / "artifact_manifests",
        replica_book_path=tmp_path / "replica_book.json",
        replica_tasks_path=tmp_path / "replica_repair_tasks.json",
        replica_storage_root=tmp_path / "storage_replicas",
        failure_actions_path=tmp_path / "candidate_failure_actions.json",
    )

    gate = binding["metadata"]["promotion_gate"]
    assert binding["status"] == "candidate"
    assert gate["ok"] is False
    assert "code_eval:no_code_records" in gate["blockers"]
    assert binding["metadata"]["failure_actions"]["actions"][0]["action_type"] == "training_retrain"


def test_try_post_treats_missing_optional_catalog_as_none(monkeypatch) -> None:
    def missing(*_args, **_kwargs):
        raise urllib.error.HTTPError("http://test/catalog/items", 404, "not found", hdrs=None, fp=None)

    monkeypatch.setattr("api.node_client.post", missing)

    assert try_post("http://test", "/catalog/items", {"name": "x"}) is None


def test_node_client_submits_candidate_failure_retrain_action(monkeypatch) -> None:
    posted = []

    def fake_post(server: str, path: str, body: dict):
        posted.append({"server": server, "path": path, "body": body})
        return {"ok": True, "job": {"id": "train_retry_1", "status": "queued"}}

    monkeypatch.setattr("api.node_client.post", fake_post)
    monkeypatch.setattr("api.node_client.mark_action_submitted", lambda action_id, response: {"action_id": action_id, "status": "submitted", "response": response})

    binding = {
        "metadata": {
            "failure_actions": {
                "actions": [
                    {
                        "action_id": "candidate_action_1",
                        "action_type": "training_retrain",
                        "status": "queued",
                        "training_job_request": {
                            "kind": "lora_micro",
                            "name": "retry",
                            "dataset_uri": "file:///tmp/train.jsonl",
                            "base_model": "ailovanta-base",
                            "max_steps": 64,
                            "notes": "retry",
                        },
                    }
                ]
            }
        }
    }

    submitted = submit_failure_actions("http://api", binding)

    assert posted[0]["path"] == "/training/jobs"
    assert posted[0]["body"]["name"] == "retry"
    assert submitted[0]["marked"]["status"] == "submitted"
