from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

LEDGER_SCHEMA = "ailovanta.continuous_training_ledger.v1"
ACTIVE_STATUSES = {"planned", "queued", "assigned", "running"}
COMPLETED_STATUSES = {"done", "completed"}


def load_ledger(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"schema_version": LEDGER_SCHEMA, "sources": {}, "datasets": {}, "batches": {}, "updated_at": None}
    return json.loads(target.read_text(encoding="utf-8-sig"))


def save_ledger(path: str | Path, ledger: dict[str, Any]) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    ledger["schema_version"] = LEDGER_SCHEMA
    ledger["updated_at"] = round(time.time(), 3)
    target.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    return ledger


def select_sources_for_training(
    sources_payload: dict[str, Any],
    ledger: dict[str, Any],
    *,
    max_sources: int,
    corpus_mode: str,
) -> dict[str, Any]:
    sources = [item for item in sources_payload.get("sources", []) if item.get("enabled", True)]
    sources.sort(key=lambda item: float(item.get("discovery_score") or 0), reverse=True)
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for source in sources:
        fingerprint = source_fingerprint(source, corpus_mode=corpus_mode)
        status = source_training_status(ledger, fingerprint)
        if status in ACTIVE_STATUSES or status in COMPLETED_STATUSES:
            skipped.append({"name": source.get("name"), "fingerprint": fingerprint, "status": status})
            continue
        selected.append({**source, "training_fingerprint": fingerprint})
        if len(selected) >= max_sources:
            break
    return {"selected": selected, "skipped": skipped, "available": len(sources)}


def write_limited_sources(source_path: str | Path, output_path: str | Path, ledger_path: str | Path, *, max_sources: int, corpus_mode: str) -> dict[str, Any]:
    payload = json.loads(Path(source_path).read_text(encoding="utf-8-sig"))
    ledger = load_ledger(ledger_path)
    selection = select_sources_for_training(payload, ledger, max_sources=max_sources, corpus_mode=corpus_mode)
    limited = {**payload, "sources": selection["selected"]}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(limited, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**selection, "output": str(output), "ledger_path": str(ledger_path)}


def record_training_batch(
    ledger_path: str | Path,
    *,
    selected_sources: list[dict[str, Any]],
    dataset_path: str | Path,
    dataset: dict[str, Any],
    job: dict[str, Any],
    ingest: dict[str, Any],
    corpus_mode: str,
) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    dataset_hash = file_sha256(dataset_path)
    batch_id = stable_id("batch_", dataset_hash)
    job_payload = job.get("job") if isinstance(job.get("job"), dict) else job
    job_id = str(job_payload.get("id") or job_payload.get("job_id") or "")
    now = round(time.time(), 3)
    batch = {
        "batch_id": batch_id,
        "dataset_hash": dataset_hash,
        "dataset_path": str(dataset_path),
        "dataset": dataset,
        "job_id": job_id,
        "status": str(job_payload.get("status") or "queued"),
        "corpus_mode": corpus_mode,
        "source_fingerprints": [source.get("training_fingerprint") or source_fingerprint(source, corpus_mode=corpus_mode) for source in selected_sources],
        "records": dataset.get("records"),
        "bytes": dataset.get("bytes"),
        "ingest": {key: ingest.get(key) for key in ["ok", "sources", "accepted_sources", "records", "bytes", "languages", "corpus_mode"]},
        "created_at": now,
        "updated_at": now,
    }
    ledger.setdefault("batches", {})[batch_id] = batch
    ledger.setdefault("datasets", {})[dataset_hash] = {"dataset_hash": dataset_hash, "batch_id": batch_id, "job_id": job_id, "status": batch["status"], "updated_at": now}
    for source in selected_sources:
        fingerprint = source.get("training_fingerprint") or source_fingerprint(source, corpus_mode=corpus_mode)
        ledger.setdefault("sources", {})[fingerprint] = {
            "fingerprint": fingerprint,
            "source_key": source_key(source),
            "source_revision": source_revision(source),
            "source_name": source.get("name"),
            "source_url": source.get("url") or source.get("path"),
            "corpus_mode": corpus_mode,
            "batch_id": batch_id,
            "job_id": job_id,
            "status": batch["status"],
            "updated_at": now,
        }
    return save_ledger(ledger_path, ledger)


def sync_ledger_with_jobs(ledger_path: str | Path, jobs: list[dict[str, Any]]) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    by_id = {str(job.get("id") or job.get("job_id") or ""): job for job in jobs}
    changed = 0
    now = round(time.time(), 3)
    for batch in ledger.get("batches", {}).values():
        job = by_id.get(str(batch.get("job_id") or ""))
        if not job:
            continue
        status = str(job.get("status") or batch.get("status") or "")
        if status and status != batch.get("status"):
            batch["status"] = status
            batch["updated_at"] = now
            dataset = ledger.get("datasets", {}).get(str(batch.get("dataset_hash") or ""))
            if dataset:
                dataset["status"] = status
                dataset["updated_at"] = now
            for fingerprint in batch.get("source_fingerprints", []):
                source = ledger.get("sources", {}).get(str(fingerprint))
                if source:
                    source["status"] = status
                    source["updated_at"] = now
            changed += 1
    if changed:
        save_ledger(ledger_path, ledger)
    return {"ok": True, "changed": changed, "summary": ledger_summary(ledger), "ledger_path": str(ledger_path)}


def ledger_summary(ledger: dict[str, Any]) -> dict[str, Any]:
    source_statuses: dict[str, int] = {}
    batch_statuses: dict[str, int] = {}
    for item in ledger.get("sources", {}).values():
        status = str(item.get("status") or "unknown")
        source_statuses[status] = source_statuses.get(status, 0) + 1
    for item in ledger.get("batches", {}).values():
        status = str(item.get("status") or "unknown")
        batch_statuses[status] = batch_statuses.get(status, 0) + 1
    return {
        "schema_version": ledger.get("schema_version") or LEDGER_SCHEMA,
        "sources": len(ledger.get("sources", {})),
        "datasets": len(ledger.get("datasets", {})),
        "batches": len(ledger.get("batches", {})),
        "source_statuses": source_statuses,
        "batch_statuses": batch_statuses,
        "updated_at": ledger.get("updated_at"),
    }


def source_training_status(ledger: dict[str, Any], fingerprint: str) -> str | None:
    item = ledger.get("sources", {}).get(fingerprint)
    return str(item.get("status")) if item else None


def source_fingerprint(source: dict[str, Any], *, corpus_mode: str) -> str:
    raw = {
        "source_key": source_key(source),
        "revision": source_revision(source),
        "corpus_mode": corpus_mode,
    }
    return stable_id("source_train_", json.dumps(raw, ensure_ascii=False, sort_keys=True))


def source_key(source: dict[str, Any]) -> str:
    return str(source.get("url") or source.get("path") or source.get("html_url") or source.get("name") or "unknown")


def source_revision(source: dict[str, Any]) -> str:
    if source.get("commit_sha"):
        return str(source.get("commit_sha"))
    if source.get("pushed_at"):
        return str(source.get("pushed_at"))
    return str(source.get("branch") or "main")


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def stable_id(prefix: str, value: str) -> str:
    return prefix + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
