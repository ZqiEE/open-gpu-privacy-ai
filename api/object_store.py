from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class ObjectStoreError(RuntimeError):
    pass


def s3_client() -> Any:
    try:
        import boto3  # type: ignore
    except Exception as exc:
        raise ObjectStoreError("boto3 missing; install requirements-object.txt") from exc
    kwargs: dict[str, Any] = {}
    endpoint = os.environ.get("AILOVANTA_S3_ENDPOINT")
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    region = os.environ.get("AILOVANTA_S3_REGION")
    if region:
        kwargs["region_name"] = region
    return boto3.client("s3", **kwargs)


def bucket_name(bucket: str | None = None) -> str:
    value = bucket or os.environ.get("AILOVANTA_S3_BUCKET")
    if not value:
        raise ObjectStoreError("bucket required; set AILOVANTA_S3_BUCKET or pass bucket")
    return value


def put_object(local_path: str, key: str, bucket: str | None = None) -> dict[str, Any]:
    path = Path(local_path)
    if not path.exists():
        raise ObjectStoreError("local path not found")
    client = s3_client()
    name = bucket_name(bucket)
    client.upload_file(str(path), name, key)
    return {"bucket": name, "key": key, "local_path": str(path), "uri": f"s3://{name}/{key}"}


def get_object(key: str, output_path: str, bucket: str | None = None) -> dict[str, Any]:
    client = s3_client()
    name = bucket_name(bucket)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(name, key, str(target))
    return {"bucket": name, "key": key, "output_path": str(target), "uri": f"s3://{name}/{key}"}


def presign_get(key: str, bucket: str | None = None, expires: int = 3600) -> dict[str, Any]:
    client = s3_client()
    name = bucket_name(bucket)
    url = client.generate_presigned_url("get_object", Params={"Bucket": name, "Key": key}, ExpiresIn=expires)
    return {"bucket": name, "key": key, "url": url, "expires": expires}
