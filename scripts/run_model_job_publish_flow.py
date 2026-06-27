from __future__ import annotations

import argparse
import json
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from api.artifact_manifest import write_chunk_manifest
from api.model_job import run_model_job
from api.wio import signed_result


def call(method: str, server: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(server.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=180) as res:
        return json.loads(res.read().decode("utf-8"))


def pack_dir(source_dir: str | Path, target_zip: str | Path) -> Path:
    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError(str(source))
    target = Path(target_zip)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if source.is_file():
            zf.write(source, source.name)
        else:
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(source))
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local model job, store artifact, create receipt, notarize, and publish")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--payload", required=True)
    parser.add_argument("--source-id", default="model_job_flow")
    parser.add_argument("--node-id", default="demo-node")
    parser.add_argument("--node-secret", default="demo-secret")
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--loose", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=8 * 1024 * 1024)
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    profile = {"cpu_threads": 1, "memory_gb": 4.0, "has_gpu": args.gpu, "gpu_name": None}
    job_result = run_model_job(payload, profile, args.source_id)

    name = job_result["name"]
    version = job_result["version"]
    artifact_id = f"{name}-{version}-{args.source_id}"
    zip_path = pack_dir(job_result["location"], Path("runtime_data/artifact_bundles") / f"{artifact_id}.zip")

    stored = call("POST", args.server, "/artifacts/store", {
        "local_path": str(zip_path),
        "artifact_id": artifact_id,
        "metadata": {"name": name, "version": version, "source_job_id": args.source_id, "kind": job_result["kind"]},
    })["artifact"]

    manifest_path = Path("runtime_data/artifact_manifests") / f"{artifact_id}.manifest.json"
    artifact_manifest = write_chunk_manifest(
        zip_path,
        stored["artifact_uri"],
        manifest_path,
        chunk_size=args.chunk_size,
        replicas=[stored["artifact_uri"]],
        metadata={"name": name, "version": version, "source_job_id": args.source_id, "kind": job_result["kind"]},
    )

    receipt = signed_result({
        "task_id": args.source_id,
        "checkpoint_uri": stored["artifact_uri"],
        "checkpoint_hash": stored["artifact_hash"],
        "artifact_manifest_uri": manifest_path.resolve().as_uri(),
        "artifact_manifest_hash": artifact_manifest["artifact_hash"],
        "token_count": int((job_result.get("metrics") or {}).get("steps") or 0),
        "train_loss": 0.0,
        "eval_loss": 0.0,
    }, node_id=args.node_id, secret=args.node_secret)

    metrics = {**job_result.get("metrics", {}), "artifact_manifest": {"uri": manifest_path.resolve().as_uri(), "chunk_count": artifact_manifest["chunk_count"], "chunk_size": artifact_manifest["chunk_size"]}}
    cataloged = call("POST", args.server, "/catalog/from-receipt", {
        "receipt": receipt,
        "name": name,
        "version": version,
        "kind": job_result["kind"],
        "metrics": metrics,
        "require_valid": not args.loose,
    })
    item_id = cataloged["item"]["id"]
    validated = call("POST", args.server, f"/catalog/items/{item_id}/validate", {})
    notarized = call("POST", args.server, f"/catalog/items/{item_id}/notarize", {})
    published = call("POST", args.server, f"/catalog/items/{item_id}/publish", {})
    readiness = call("GET", args.server, "/ops/readiness", None)

    print(json.dumps({
        "ok": True,
        "job_result": job_result,
        "bundle": str(zip_path),
        "artifact": stored,
        "artifact_manifest": artifact_manifest,
        "artifact_manifest_path": str(manifest_path),
        "receipt": receipt,
        "cataloged": cataloged,
        "validated": validated,
        "notarized": notarized,
        "published": published,
        "readiness": readiness,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
