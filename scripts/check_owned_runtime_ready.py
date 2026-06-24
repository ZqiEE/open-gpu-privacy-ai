from __future__ import annotations

import os
import sys

import httpx


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"missing env: {name}")
    return value


def get_json(url: str) -> dict:
    with httpx.Client(timeout=10) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def main() -> int:
    api_url = os.getenv("AILOVANTA_API_URL", "http://127.0.0.1:8000").rstrip("/")
    worker_url = require_env("AILOVANTA_DEFAULT_WORKER_URL").rstrip("/")

    print("checking api", api_url)
    api_status = get_json(api_url + "/runtime/status")
    print("runtime status", api_status)

    print("checking worker", worker_url)
    worker_status = get_json(worker_url + "/health")
    print("worker status", worker_status)

    if api_status.get("models", 0) < 1:
        raise RuntimeError("no runtime model registered")
    if api_status.get("runtimes", 0) < 1:
        raise RuntimeError("no runtime node registered")
    if not worker_status.get("ok"):
        raise RuntimeError("worker is not ready")

    print("owned runtime readiness: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("owned runtime readiness: failed", exc, file=sys.stderr)
        raise SystemExit(1)
