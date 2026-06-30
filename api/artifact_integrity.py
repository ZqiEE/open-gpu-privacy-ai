from __future__ import annotations

from pathlib import Path

from api.artifact_hash import sha256_path
from api.artifact_fetch import fetch_artifact, sha256_file
from api.content_gateway import fetch_content_uri
from api.object_store import get_object
from api.runtime_ref import to_local_path


def normalize_hash(value: str | None) -> str:
    if not value:
        return ""
    return value if value.startswith("sha256:") else "sha256:" + value


def cache_dir_for(uri: str, root: str = "runtime_data/artifact_verify") -> Path:
    safe = uri.replace("://", "_").replace("/", "_").replace(":", "_")[:160]
    path = Path(root) / safe
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_for_verify(uri: str, cache_root: str = "runtime_data/artifact_verify") -> dict:
    cache = cache_dir_for(uri, cache_root)
    if uri.startswith("file://"):
        path = to_local_path(uri)
        if path is None:
            return {"ok": False, "reason": "bad_file_uri", "uri": uri}
        if not path.exists():
            return {"ok": False, "reason": "file_artifact_not_found", "uri": uri}
        return {"ok": True, "uri": uri, "path": str(path), "kind": "directory" if path.is_dir() else "file"}
    if uri.startswith("s3://"):
        bucket_key = uri.removeprefix("s3://")
        if "/" not in bucket_key:
            return {"ok": False, "reason": "bad_s3_uri", "uri": uri}
        bucket, key = bucket_key.split("/", 1)
        target = cache / Path(key).name
        obj = get_object(key, str(target), bucket)
        return {"ok": True, "uri": uri, "path": obj["output_path"], "kind": "s3", "object": obj}
    if uri.startswith("ipfs://"):
        item = fetch_content_uri(uri, str(cache))
        return {"ok": True, "uri": uri, "path": item["path"], "kind": "content_gateway", "artifact": item}
    if uri.startswith(("http://", "https://")):
        item = fetch_artifact(uri, str(cache), extract=False)
        return {"ok": True, "uri": uri, "path": item["path"], "kind": "http", "artifact": item}
    return {"ok": False, "reason": "unsupported_artifact_uri", "uri": uri}


def verify_artifact_uri(uri: str, expected_hash: str, cache_root: str = "runtime_data/artifact_verify") -> dict:
    expected = normalize_hash(expected_hash)
    if not uri:
        return {"ok": False, "reason": "missing_artifact_uri"}
    if not expected:
        return {"ok": False, "reason": "missing_expected_hash", "uri": uri}
    fetched = fetch_for_verify(uri, cache_root=cache_root)
    if not fetched.get("ok"):
        return fetched
    path = Path(fetched["path"])
    actual = sha256_path(path) if path.is_dir() else "sha256:" + sha256_file(path)
    ok = actual == expected
    return {"ok": ok, "uri": uri, "path": str(path), "expected_hash": expected, "actual_hash": actual, "reason": "ok" if ok else "artifact_hash_mismatch", "kind": fetched.get("kind")}


def verify_catalog_item(item: dict, cache_root: str = "runtime_data/artifact_verify") -> dict:
    uri = str(item.get("artifact_uri") or item.get("location") or "")
    expected = str(item.get("artifact_hash") or item.get("digest") or "")
    result = verify_artifact_uri(uri, expected, cache_root=cache_root)
    return {"item_id": item.get("id"), "name": item.get("name"), "version": item.get("version"), **result}
