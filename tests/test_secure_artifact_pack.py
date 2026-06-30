import json
from pathlib import Path

import pytest

from api.replica_book import status as replica_status
from api.secure_artifact_pack import generate_artifact_key, package_secure_model_directory, restore_secure_model_directory

pytest.importorskip("cryptography")


def test_secure_model_directory_package_encrypts_chunks_and_restores(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(json.dumps({"model_type": "ailovanta-test"}), encoding="utf-8")
    (model_dir / "adapter_model.safetensors").write_bytes(b"secret-model-weights" * 20)
    key = generate_artifact_key()

    package = package_secure_model_directory(
        model_dir,
        output_root=tmp_path / "secure_artifacts",
        manifest_dir=tmp_path / "manifests",
        replica_book_path=tmp_path / "replica_book.json",
        key=key,
        key_id="test-key",
        chunk_size=64,
    )

    manifest = package["manifest"]
    assert package["ok"] is True
    assert manifest["sealed"] is True
    assert manifest["anti_theft"]["key_in_manifest"] is False
    assert manifest["artifact_hash"].startswith("sha256:")
    assert manifest["plaintext_artifact_hash"].startswith("sha256:")
    assert manifest["artifact_hash"] != manifest["plaintext_artifact_hash"]
    assert "test-key" in json.dumps(manifest)
    assert key not in json.dumps(manifest)
    assert replica_status(tmp_path / "replica_book.json")["artifact_count"] == 1

    encrypted_sources = [Path(chunk["sources"][0].removeprefix("file://")) for chunk in manifest["chunks"]]
    assert encrypted_sources
    assert all(path.exists() for path in encrypted_sources)
    assert b"secret-model-weights" not in b"".join(path.read_bytes() for path in encrypted_sources)

    restored = tmp_path / "restored"
    result = restore_secure_model_directory(manifest, restored, key=key)

    assert result["ok"] is True
    assert (restored / "config.json").read_text(encoding="utf-8") == (model_dir / "config.json").read_text(encoding="utf-8")
    assert (restored / "adapter_model.safetensors").read_bytes() == (model_dir / "adapter_model.safetensors").read_bytes()


def test_secure_model_directory_requires_key_for_restore(tmp_path: Path) -> None:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "weights.bin").write_bytes(b"owned-weights")
    package = package_secure_model_directory(
        model_dir,
        output_root=tmp_path / "secure_artifacts",
        manifest_dir=tmp_path / "manifests",
        replica_book_path=tmp_path / "replica_book.json",
        key=generate_artifact_key(),
        chunk_size=8,
    )

    with pytest.raises(Exception):
        restore_secure_model_directory(package["manifest"], tmp_path / "restored", key=generate_artifact_key())
