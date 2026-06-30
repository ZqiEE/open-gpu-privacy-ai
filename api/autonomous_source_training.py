from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

from api.github_code_ingest import ingest_sources


def post_json(server: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        server.rstrip("/") + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def run_autonomous_source_training_cycle(
    server: str = "http://127.0.0.1:8000",
    sources_path: str | Path = "runtime_data/github_code_sources.json",
    work_root: str | Path = "runtime_data/autonomous_source_training",
    discover: bool = True,
    fetch: bool = True,
    max_sources: int = 3,
    max_records: int = 512,
    corpus_mode: str = "mixed",
    max_steps: int = 16,
) -> dict[str, Any]:
    root = Path(work_root)
    root.mkdir(parents=True, exist_ok=True)
    sources = Path(sources_path)

    discovery = discover_sources_if_needed(sources, enabled=discover)
    limited_sources = limit_sources(sources, root / "sources_limited.json", max_sources)
    corpus_path = root / "code_corpus.jsonl"
    ingest = ingest_sources(
        limited_sources,
        target_root=root / "source_repos",
        corpus_output=corpus_path,
        rights_path=root / "rights_proofs.json",
        jobs_path=root / "code_training_jobs.json",
        fetch=fetch,
        create_job=False,
        corpus_mode=corpus_mode,
    )
    dataset_path = root / "autonomous_training_dataset.jsonl"
    dataset = corpus_to_training_dataset(corpus_path, dataset_path, max_records=max_records)
    if dataset["records"] <= 0:
        return {
            "ok": False,
            "stage": "no_training_records",
            "discovery": discovery,
            "ingest": compact_ingest(ingest),
            "dataset": dataset,
        }

    job = post_json(
        server,
        "/training/jobs",
        {
            "kind": "lora_micro",
            "name": "ailovanta-auto-source",
            "dataset_uri": "file://" + str(dataset_path.resolve()),
            "base_model": "ailovanta-auto-bootstrap",
            "max_steps": max_steps,
            "notes": "autonomous source discovery -> ingest -> training job",
        },
    )
    return {
        "ok": True,
        "stage": "training_job_queued",
        "server": server,
        "discovery": discovery,
        "ingest": compact_ingest(ingest),
        "dataset": dataset,
        "job": job,
        "created_at": round(time.time(), 3),
    }


def discover_sources_if_needed(output_path: Path, enabled: bool) -> dict[str, Any]:
    if output_path.exists() and not enabled:
        return {"ok": True, "enabled": False, "reason": "existing_sources", "output": str(output_path)}
    if not enabled and not output_path.exists():
        raise FileNotFoundError("sources file not found and discovery disabled: " + str(output_path))

    from scripts.discover_github_sources import DEFAULT_QUERIES, load_manifest, save_manifest, search_repositories, source_from_repo, upsert_sources

    import os

    token = os.getenv("GITHUB_TOKEN")
    manifest = load_manifest(output_path)
    discovered = []
    for query in DEFAULT_QUERIES[:3]:
        repos = search_repositories(query, pages=1, per_page=10, token=token)
        discovered.extend(source_from_repo(repo, "authorized_unrestricted", "operator authorized autonomous GitHub source discovery") for repo in repos)
    added = upsert_sources(manifest, discovered)
    save_manifest(output_path, manifest)
    return {
        "ok": True,
        "enabled": True,
        "queries": DEFAULT_QUERIES[:3],
        "discovered": len(discovered),
        "added": added,
        "total_sources": len(manifest.get("sources", [])),
        "output": str(output_path),
    }


def limit_sources(source_path: Path, output_path: Path, max_sources: int) -> Path:
    payload = json.loads(source_path.read_text(encoding="utf-8-sig"))
    sources = [item for item in payload.get("sources", []) if item.get("enabled", True)]
    limited = {**payload, "sources": sources[:max_sources]}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(limited, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def corpus_to_training_dataset(corpus_path: str | Path, output_path: str | Path, max_records: int = 512) -> dict[str, Any]:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = 0
    bytes_written = 0
    with Path(corpus_path).open("r", encoding="utf-8") as source, output.open("w", encoding="utf-8") as target:
        for line in source:
            if records >= max_records:
                break
            if not line.strip():
                continue
            item = json.loads(line)
            text = training_text_from_record(item)
            if not text:
                continue
            payload = {
                "text": text,
                "source_path": item.get("path"),
                "source_name": item.get("source_name"),
                "rights_id": item.get("rights_id"),
                "record_kind": item.get("training_record_kind"),
            }
            encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            target.write(encoded + "\n")
            records += 1
            bytes_written += len(encoded.encode("utf-8", errors="ignore"))
    return {"ok": records > 0, "output": str(output), "records": records, "bytes": bytes_written}


def training_text_from_record(item: dict[str, Any]) -> str:
    if item.get("training_record_kind") == "instruction":
        parts = [
            "Instruction: " + str(item.get("instruction") or "").strip(),
            "Context: " + str(item.get("context") or "").strip()[:6000],
            "Expected: " + str(item.get("expected_response") or "").strip(),
        ]
        return "\n\n".join(part for part in parts if len(part.strip()) > 12).strip()
    text = str(item.get("text") or item.get("content") or "").strip()
    if text:
        return text[:8000]
    return ""


def compact_ingest(ingest: dict[str, Any]) -> dict[str, Any]:
    keys = ["ok", "sources", "accepted_sources", "records", "bytes", "languages", "corpus_output", "corpus_mode"]
    return {key: ingest.get(key) for key in keys}
