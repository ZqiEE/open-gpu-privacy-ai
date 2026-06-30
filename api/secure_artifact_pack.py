from __future__ import annotations

import base64
import hashlib
import json
import os
import tarfile
import tempfile
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:  # pragma: no cover - CI/minimal installs may omit optional crypto.
    AESGCM = None  # type: ignore[assignment]

from api.chunk_manifest import manifest_hash
from api.replica_book import add_manifest, status as replica_status

SCHEMA = "ailovanta.secure_artifact_manifest.v1"
DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024


class SecureArtifactError(RuntimeError):
    pass


def generate_artifact_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


def package_secure_model_directory(
    model_dir: str | Path,
    *,
    output_root: str | Path = "runtime_data/secure_artifacts",
    manifest_dir: str | Path = "runtime_data/artifact_manifests",
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    key: str | bytes | None = None,
    key_id: str = "local-artifact-key",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    storage_node_id: str = "local-secure-storage",
) -> dict[str, Any]:
    source = Path(model_dir)
    if not source.exists() or not source.is_dir():
        raise SecureArtifactError("model_dir must be an existing directory")
    _require_crypto()
    artifact_id = "artifact_secure_" + uuid4().hex[:12]
    aes_key = _resolve_key(key)
    out_root = Path(output_root)
    chunk_root = out_root / storage_node_id / artifact_id
    chunk_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ailovanta-secure-pack-") as tmp:
        tar_path = Path(tmp) / "model.tar"
        _write_tar(source, tar_path)
        manifest = _encrypt_tar_to_chunks(
            tar_path,
            artifact_id=artifact_id,
            chunk_root=chunk_root,
            aes_key=aes_key,
            key_id=key_id,
            chunk_size=chunk_size,
            storage_node_id=storage_node_id,
        )

    manifest_path = Path(manifest_dir) / f"{artifact_id}.secure.manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest["manifest_uri"] = "file://" + str(manifest_path.resolve())
    manifest["manifest_hash"] = manifest_hash(manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    book = add_manifest(manifest, node_id=storage_node_id, path=replica_book_path)
    return {
        "ok": True,
        "schema_version": "ailovanta.secure_artifact_package.v1",
        "artifact_id": artifact_id,
        "manifest_uri": manifest["manifest_uri"],
        "manifest": manifest,
        "replica_book_path": str(Path(replica_book_path)),
        "replica_status": replica_status(replica_book_path),
        "book": book,
    }


def restore_secure_model_directory(
    manifest: dict[str, Any] | str | Path,
    output_dir: str | Path,
    *,
    key: str | bytes | None = None,
) -> dict[str, Any]:
    payload = _load_manifest(manifest)
    _require_crypto()
    aes_key = _resolve_key(key)
    chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else []
    if not chunks:
        raise SecureArtifactError("secure artifact manifest has no chunks")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ailovanta-secure-restore-") as tmp:
        tar_path = Path(tmp) / "model.tar"
        plaintext_hash = hashlib.sha256()
        with tar_path.open("wb") as handle:
            for chunk in sorted(chunks, key=lambda item: int(item.get("index") or 0)):
                encrypted_path = _first_file_source(chunk)
                encrypted = encrypted_path.read_bytes()
                if _sha256(encrypted) != chunk.get("sha256"):
                    raise SecureArtifactError("encrypted chunk hash mismatch: " + str(chunk.get("chunk_id")))
                plaintext = AESGCM(aes_key).decrypt(  # type: ignore[operator]
                    base64.b64decode(str(chunk["nonce"])),
                    encrypted,
                    _aad(payload["artifact_id"], int(chunk["index"]), str(chunk["plaintext_sha256"])),
                )
                if _sha256(plaintext) != chunk.get("plaintext_sha256"):
                    raise SecureArtifactError("plaintext chunk hash mismatch: " + str(chunk.get("chunk_id")))
                plaintext_hash.update(plaintext)
                handle.write(plaintext)
        if "plaintext_artifact_hash" in payload and "sha256:" + plaintext_hash.hexdigest() != payload["plaintext_artifact_hash"]:
            raise SecureArtifactError("plaintext artifact hash mismatch")
        _safe_extract_tar(tar_path, out_dir)
    return {"ok": True, "output_dir": str(out_dir), "artifact_id": payload.get("artifact_id")}


def _encrypt_tar_to_chunks(
    tar_path: Path,
    *,
    artifact_id: str,
    chunk_root: Path,
    aes_key: bytes,
    key_id: str,
    chunk_size: int,
    storage_node_id: str,
) -> dict[str, Any]:
    plaintext_artifact_hash = hashlib.sha256()
    encrypted_artifact_hash = hashlib.sha256()
    chunks: list[dict[str, Any]] = []
    with tar_path.open("rb") as handle:
        index = 0
        while True:
            plaintext = handle.read(chunk_size)
            if not plaintext:
                break
            plaintext_hash = _sha256(plaintext)
            nonce = os.urandom(12)
            encrypted = AESGCM(aes_key).encrypt(nonce, plaintext, _aad(artifact_id, index, plaintext_hash))  # type: ignore[operator]
            encrypted_hash = _sha256(encrypted)
            plaintext_artifact_hash.update(plaintext)
            encrypted_artifact_hash.update(encrypted)
            target = chunk_root / f"chunk_{index:06d}.enc"
            target.write_bytes(encrypted)
            chunks.append(
                {
                    "chunk_id": f"chunk_{index:06d}",
                    "index": index,
                    "size_bytes": len(encrypted),
                    "plaintext_size_bytes": len(plaintext),
                    "sha256": encrypted_hash,
                    "plaintext_sha256": plaintext_hash,
                    "nonce": base64.b64encode(nonce).decode("ascii"),
                    "sources": ["file://" + str(target.resolve())],
                    "encryption": {"algorithm": "AES-256-GCM", "key_id": key_id, "key_material": "not_in_manifest"},
                }
            )
            index += 1
    return {
        "schema_version": SCHEMA,
        "artifact_id": artifact_id,
        "artifact_hash": "sha256:" + encrypted_artifact_hash.hexdigest(),
        "plaintext_artifact_hash": "sha256:" + plaintext_artifact_hash.hexdigest(),
        "artifact_name": tar_path.name,
        "artifact_bytes": sum(int(chunk["size_bytes"]) for chunk in chunks),
        "plaintext_artifact_bytes": tar_path.stat().st_size,
        "created_at": time(),
        "sealed": True,
        "anti_theft": {
            "storage_nodes_receive": "encrypted_chunks_only",
            "key_in_manifest": False,
            "runtime_requires": "authorized_key_release",
        },
        "chunks": chunks,
        "replica_policy": {"min_replicas": 3, "source_types": ["encrypted_node_cache", "regional_mirror", "content_addressed"]},
    }


def _resolve_key(value: str | bytes | None) -> bytes:
    raw = value or os.getenv("AILOVANTA_ARTIFACT_ENCRYPTION_KEY")
    if raw is None:
        raise SecureArtifactError("missing artifact encryption key")
    if isinstance(raw, bytes):
        key = raw
    else:
        text = raw.strip()
        try:
            key = base64.urlsafe_b64decode(text)
        except Exception:
            key = bytes.fromhex(text)
    if len(key) not in {16, 24, 32}:
        raise SecureArtifactError("artifact encryption key must be 128, 192, or 256 bits")
    return key


def _require_crypto() -> None:
    if AESGCM is None:
        raise SecureArtifactError("cryptography package is required for sealed model artifacts")


def _write_tar(source: Path, target: Path) -> None:
    with tarfile.open(target, "w") as archive:
        for item in sorted(source.rglob("*")):
            if item.is_file():
                archive.add(item, arcname=item.relative_to(source))


def _safe_extract_tar(tar_path: Path, output_dir: Path) -> None:
    root = output_dir.resolve()
    with tarfile.open(tar_path, "r") as archive:
        for member in archive.getmembers():
            target = (output_dir / member.name).resolve()
            if root != target and root not in target.parents:
                raise SecureArtifactError("unsafe tar member path: " + member.name)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise SecureArtifactError("could not read tar member: " + member.name)
                target.write_bytes(extracted.read())


def _first_file_source(chunk: dict[str, Any]) -> Path:
    sources = chunk.get("sources") if isinstance(chunk.get("sources"), list) else []
    for source in sources:
        raw = str(source)
        if raw.startswith("file://"):
            path = Path(raw.removeprefix("file://"))
            if path.exists() and path.is_file():
                return path
    raise SecureArtifactError("encrypted chunk has no local file source")


def _load_manifest(value: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    path = Path(str(value).removeprefix("file://"))
    return json.loads(path.read_text(encoding="utf-8"))


def _aad(artifact_id: str, index: int, plaintext_hash: str) -> bytes:
    return f"{artifact_id}:{index}:{plaintext_hash}".encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
