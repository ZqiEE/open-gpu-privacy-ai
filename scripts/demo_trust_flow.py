from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from api.artifact_store import file_sha256
from api.wio import signed_result


def post(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        server.rstrip("/") + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.loads(res.read().decode("utf-8"))


def make_demo_file(path: Path, name: str, version: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "ailovanta.demo_artifact.v1",
        "name": name,
        "version": version,
        "message": "demo model metadata artifact",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run artifact -> receipt -> catalog -> notarize -> publish -> runtime load demo")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--name", default="ailovanta-demo")
    parser.add_argument("--version", default="v0-trust-demo")
    parser.add_argument("--node-id", default="demo-node")
    parser.add_argument("--node-secret", default="demo-secret")
    parser.add_argument("--artifact-path", default="runtime_data/trust_demo/output.json")
    parser.add_argument("--require-valid", action="store_true")
    args = parser.parse_args()

    path = make_demo_file(Path(args.artifact_path), args.name, args.version)
    digest = file_sha256(path)

    stored = post(args.server, "/artifacts/store", {
        "local_path": str(path),
        "artifact_id": f"{args.name}-{args.version}",
        "metadata": {"name": args.name, "version": args.version},
    })["artifact"]

    receipt = signed_result({
        "task_id": "task_demo_trust_flow",
        "checkpoint_uri": stored["artifact_uri"],
        "checkpoint_hash": stored.get("artifact_hash") or digest,
        "token_count": 128,
        "train_loss": 0.1,
        "eval_loss": 0.1,
    }, node_id=args.node_id, secret=args.node_secret)

    cataloged = post(args.server, "/catalog/from-receipt", {
        "receipt": receipt,
        "name": args.name,
        "version": args.version,
        "kind": "adapter",
        "metrics": {"score": 0.8, "demo": True},
        "require_valid": bool(args.require_valid),
    })
    item_id = cataloged["item"]["id"]

    validated = post(args.server, f"/catalog/items/{item_id}/validate", {})
    notarized = post(args.server, f"/catalog/items/{item_id}/notarize", {})
    published = post(args.server, f"/catalog/items/{item_id}/publish", {})
    loaded = post(args.server, "/runtime/local/load", {"item_id": item_id})
    generated = post(args.server, "/runtime/local/generate", {
        "model_key": f"{args.name}:{args.version}",
        "prompt": "Say hello from Ailovanta trust flow.",
        "max_new_tokens": 32,
    })

    print(json.dumps({
        "ok": True,
        "artifact": stored,
        "receipt": receipt,
        "catalog": cataloged,
        "validated": validated,
        "notarized": notarized,
        "published": published,
        "loaded": loaded,
        "generated": generated,
        "note": "For strict proof validation, run API with AILOVANTA_NODE_SECRETS_JSON containing the same node secret and pass --require-valid.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
