from __future__ import annotations

import os
from pathlib import Path

from api.artifact_fetch import fetch_artifact


def content_uri_to_url(uri: str) -> str:
    if uri.startswith("ipfs://"):
        path = uri.removeprefix("ipfs://").strip("/")
        base = os.environ.get("AILOVANTA_CONTENT_GATEWAY", "https://ipfs.io/ipfs").rstrip("/")
        return f"{base}/{path}"
    return uri


def fetch_content_uri(uri: str, output_dir: str) -> dict:
    url = content_uri_to_url(uri)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return fetch_artifact(url, output_dir, extract=True)
