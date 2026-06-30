import json
import urllib.error
from pathlib import Path

import pytest

from api.artifact_hash import sha256_path
from api.artifact_integrity import verify_artifact_uri
from api.model_job import resolve_dataset_path, run_model_job
from api.node_client import make_output, submit_failure_actions, try_post
from api.secure_artifact_pack import generate_artifact_key
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


def test_run_model_job_strict_real_training_does_not_fallback_to_lightweight(tmp_path: Path) -> None:
    dataset = write_dataset(tmp_path / "train.jsonl")
    output_dir = tmp_path / "strict-model"

    result = run_model_job(
        {
            "name": "strict-real",
            "version": "v1",
            "dataset_uri": "file://" + str(dataset),
            "base_model": str(tmp_path / "missing-base-model"),
            "max_steps": 1,
            "output_dir": str(output_dir),
            "real": True,
            "use_transformers": True,
            "peft": True,
            "lora": True,
            "allow_lightweight_fallback": False,
        },
        {"cpu_threads": 4, "memory_gb": 16, "has_gpu": True},
        "job-strict-real",
    )

    record = json.loads((output_dir / "output.json").read_text(encoding="utf-8"))

    assert result["status"] == "failed"
    assert result["metrics"]["backend"] == "real_training_preflight_failed"
    assert result["metrics"]["score"] == 0.0
    assert not (output_dir / "ngram_model.json").exists()
    assert record["kind"] == "training_failed"
    assert record["real_training_preflight"]["ok"] is False
    assert "base_model_path_missing" in record["real_training_preflight"]["blockers"]


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


def test_directory_artifact_integrity_uses_deterministic_tree_hash(tmp_path: Path) -> None:
    model_dir = tmp_path / "model-dir"
    model_dir.mkdir()
    (model_dir / "config.json").write_text('{"model_type":"gpt2"}', encoding="utf-8")
    nested = model_dir / "tokenizer"
    nested.mkdir()
    (nested / "tokenizer_config.json").write_text("{}", encoding="utf-8")

    expected = sha256_path(model_dir)
    result = verify_artifact_uri(model_dir.resolve().as_uri(), expected)

    assert result["ok"] is True
    assert result["kind"] == "directory"
    assert result["actual_hash"] == expected


def test_bind_local_training_artifact_registers_transformers_directory_candidate(tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("cryptography")
    dataset = write_dataset(tmp_path / "train.jsonl")
    output_dir = tmp_path / "transformers-model"
    output_dir.mkdir()
    (output_dir / "config.json").write_text('{"model_type":"gpt2"}', encoding="utf-8")
    (output_dir / "tokenizer_config.json").write_text("{}", encoding="utf-8")
    record = {
        "schema": "ailovanta.model_output.v1",
        "name": "real-transformers",
        "version": "v1",
        "source_job_id": "job-transformers-dir",
        "base_model": "local-base",
        "dataset_uri": "file://" + str(dataset),
        "data_path": "file://" + str(dataset),
        "kind": "full_model",
        "location": str(output_dir),
        "metrics": {"backend": "transformers", "score": 0.8},
        "backend_message": "local transformers run finished",
    }
    (output_dir / "output.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    monkeypatch.setenv("AILOVANTA_ARTIFACT_ENCRYPTION_KEY", generate_artifact_key())

    from api.artifact_binding import ArtifactBindingStore

    binding = bind_local_training_artifact(
        {
            "name": "real-transformers",
            "version": "v1",
            "source_job_id": "job-transformers-dir",
            "location": str(output_dir),
            "kind": "full_model",
            "metrics": {"backend": "transformers", "score": 0.8},
            "status": "candidate",
            "notes": "local transformers run finished",
        },
        ArtifactBindingStore(tmp_path / "bindings.sqlite3"),
        manifest_dir=tmp_path / "artifact_manifests",
        replica_book_path=tmp_path / "replica_book.json",
        replica_tasks_path=tmp_path / "replica_repair_tasks.json",
        replica_storage_root=tmp_path / "storage_replicas",
        failure_actions_path=tmp_path / "candidate_failure_actions.json",
    )

    assert binding is not None
    assert binding["backend_kind"] == "transformers-local"
    assert binding["backend_ref"] == output_dir.resolve().as_uri()
    assert binding["artifact_hash"] == sha256_path(output_dir)
    assert binding["status"] == "candidate"
    distribution = binding["metadata"]["artifact_distribution"]
    assert distribution["sealed"] is True
    assert distribution["storage_artifact_hash"].startswith("sha256:")
    gate = binding["metadata"]["promotion_gate"]
    assert gate["model_eval"]["backend"] == "transformers"
    assert gate["code_eval"]["ok"] is True
    assert gate["artifact_integrity"]["ok"] is True
    assert gate["ok"] is False
    assert any(item.startswith("code_generation:") for item in gate["blockers"])


def test_bind_local_training_artifact_ignores_failed_real_output(tmp_path: Path) -> None:
    output_dir = tmp_path / "failed-model"
    output_dir.mkdir()
    (output_dir / "output.json").write_text(
        json.dumps({"schema": "ailovanta.model_output.v1", "kind": "training_failed", "metrics": {"backend": "real_training_preflight_failed"}}),
        encoding="utf-8",
    )

    assert (
        bind_local_training_artifact(
            {
                "source_job_id": "job-failed-real",
                "location": str(output_dir),
                "metrics": {"backend": "real_training_preflight_failed"},
                "status": "failed",
            }
        )
        is None
    )


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
