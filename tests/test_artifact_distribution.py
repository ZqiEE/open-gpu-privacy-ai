from pathlib import Path

import pytest

from api.artifact_distribution import distribution_metadata, prepare_local_artifact_distribution
from api.secure_artifact_pack import generate_artifact_key


def test_prepare_local_artifact_distribution(tmp_path: Path) -> None:
    artifact_path = tmp_path / "model.bin"
    artifact_path.write_bytes(b"model-bytes")
    artifact = {
        "artifact_id": "artifact_local_1",
        "artifact_hash": "sha256:not-the-storage-hash",
        "checkpoint_uri": "file://" + str(artifact_path),
    }

    distribution = prepare_local_artifact_distribution(
        artifact,
        "file://" + str(artifact_path),
        manifest_dir=tmp_path / "manifests",
        replica_book_path=tmp_path / "replica_book.json",
        storage_node_id="storage-local-1",
    )

    assert distribution is not None
    assert distribution["schema_version"] == "ailovanta.artifact_distribution.v1"
    assert distribution["manifest_hash"].startswith("sha256:")
    assert distribution["storage_artifact_hash"].startswith("sha256:")
    assert distribution["hash_matches_model_artifact"] is False
    assert Path(distribution["manifest_uri"].removeprefix("file://")).exists()
    assert distribution["replica_status"]["artifact_count"] == 1
    assert "book" not in distribution_metadata(distribution)


def test_prepare_local_artifact_distribution_seals_model_directory(tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("cryptography")
    model_dir = tmp_path / "model-dir"
    model_dir.mkdir()
    (model_dir / "config.json").write_text('{"model_type":"ailovanta"}', encoding="utf-8")
    (model_dir / "adapter_model.safetensors").write_bytes(b"private-model-weights")
    monkeypatch.setenv("AILOVANTA_ARTIFACT_ENCRYPTION_KEY", generate_artifact_key())
    artifact = {
        "artifact_id": "artifact_model_dir_1",
        "artifact_hash": "sha256:model-record-hash",
        "checkpoint_uri": "file://" + str(model_dir),
        "artifact_key_id": "test-key-id",
    }

    distribution = prepare_local_artifact_distribution(
        artifact,
        "file://" + str(model_dir),
        manifest_dir=tmp_path / "manifests",
        replica_book_path=tmp_path / "replica_book.json",
        storage_node_id="storage-secure-1",
    )

    assert distribution is not None
    assert distribution["sealed"] is True
    assert distribution["anti_theft"]["key_in_manifest"] is False
    assert distribution["manifest"]["schema_version"] == "ailovanta.secure_artifact_manifest.v1"
    assert distribution["plaintext_artifact_hash"].startswith("sha256:")
    assert distribution["replica_status"]["artifact_count"] == 1


def test_prepare_local_artifact_distribution_requires_key_for_model_directory(tmp_path: Path, monkeypatch) -> None:
    model_dir = tmp_path / "model-dir"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.delenv("AILOVANTA_ARTIFACT_ENCRYPTION_KEY", raising=False)

    distribution = prepare_local_artifact_distribution(
        {"artifact_id": "artifact_model_dir_2", "artifact_hash": "sha256:model-record-hash", "checkpoint_uri": "file://" + str(model_dir)},
        "file://" + str(model_dir),
        manifest_dir=tmp_path / "manifests",
        replica_book_path=tmp_path / "replica_book.json",
    )

    assert distribution is None
