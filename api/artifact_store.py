from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from api.prod_config import load_config


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class StoredArtifact:
    artifact_uri: str
    artifact_hash: str
    store: str
    size_bytes: int
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_uri": self.artifact_uri,
            "artifact_hash": self.artifact_hash,
            "store": self.store,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }


class ArtifactStore(Protocol):
    def put_file(self, path: str | Path, artifact_id: str, metadata: dict[str, Any] | None = None) -> StoredArtifact:
        ...


class LocalArtifactStore:
    def __init__(self, root: str | Path = "runtime_data/artifacts") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_file(self, path: str | Path, artifact_id: str, metadata: dict[str, Any] | None = None) -> StoredArtifact:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        safe_id = artifact_id.replace("/", "_").replace(":", "_")
        target_dir = self.root / safe_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        shutil.copy2(source, target)
        digest = file_sha256(target)
        artifact_uri = target.resolve().as_uri()
        meta = {"source_path": str(source), **(metadata or {})}
        (target_dir / "metadata.json").write_text(json.dumps({"artifact_hash": digest, "artifact_uri": artifact_uri, "metadata": meta}, ensure_ascii=False, indent=2), encoding="utf-8")
        return StoredArtifact(artifact_uri=artifact_uri, artifact_hash=digest, store="local", size_bytes=target.stat().st_size, metadata=meta)


class S3CompatibleArtifactStore:
    def __init__(self, uri: str | None = None) -> None:
        self.uri = uri
        self.bucket = os.environ.get("AILOVANTA_S3_BUCKET") or self._bucket_from_uri(uri)
        if not self.bucket:
            raise RuntimeError("AILOVANTA_S3_BUCKET is required for S3-compatible artifact storage")

    @staticmethod
    def _bucket_from_uri(uri: str | None) -> str | None:
        if not uri or not uri.startswith("s3://"):
            return None
        return uri.removeprefix("s3://").split("/", 1)[0]

    def client(self) -> Any:
        try:
            import boto3  # type: ignore
        except Exception as exc:
            raise RuntimeError("boto3 is required for S3/R2/MinIO artifact storage") from exc
        kwargs: dict[str, Any] = {}
        endpoint = os.environ.get("AILOVANTA_S3_ENDPOINT")
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        region = os.environ.get("AILOVANTA_S3_REGION")
        if region:
            kwargs["region_name"] = region
        return boto3.client("s3", **kwargs)

    def put_file(self, path: str | Path, artifact_id: str, metadata: dict[str, Any] | None = None) -> StoredArtifact:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(str(source))
        digest = file_sha256(source)
        safe_id = artifact_id.replace("/", "_").replace(":", "_")
        key_prefix = os.environ.get("AILOVANTA_S3_PREFIX", "artifacts").strip("/")
        key = f"{key_prefix}/{safe_id}/{source.name}"
        extra = {"Metadata": {"artifact_hash": digest.replace("sha256:", "")}}
        self.client().upload_file(str(source), self.bucket, key, ExtraArgs=extra)
        meta = {"source_path": str(source), "s3_bucket": self.bucket, "s3_key": key, **(metadata or {})}
        return StoredArtifact(artifact_uri=f"s3://{self.bucket}/{key}", artifact_hash=digest, store="s3-compatible", size_bytes=source.stat().st_size, metadata=meta)


class ExternalArtifactStore(S3CompatibleArtifactStore):
    pass


def get_artifact_store() -> ArtifactStore:
    cfg = load_config()
    if cfg.artifact_store == "local":
        return LocalArtifactStore(cfg.artifact_store_uri or "runtime_data/artifacts")
    if cfg.artifact_store in {"s3", "r2", "minio", "object", "external"}:
        return S3CompatibleArtifactStore(cfg.artifact_store_uri)
    return ExternalArtifactStore(cfg.artifact_store_uri)
