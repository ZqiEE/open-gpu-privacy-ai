import json
from pathlib import Path

from api.continuous_training_ledger import (
    load_ledger,
    record_training_batch,
    select_sources_for_training,
    source_fingerprint,
    sync_ledger_with_jobs,
)


def _source(name: str, score: int, pushed_at: str = "2026-01-01T00:00:00Z") -> dict:
    return {
        "name": name,
        "url": f"https://github.com/demo/{name}.git",
        "branch": "main",
        "pushed_at": pushed_at,
        "enabled": True,
        "discovery_score": score,
    }


def test_select_sources_skips_queued_fingerprints() -> None:
    high = _source("high", 100)
    low = _source("low", 1)
    fingerprint = source_fingerprint(high, corpus_mode="mixed")
    ledger = {"sources": {fingerprint: {"status": "queued"}}}

    selected = select_sources_for_training({"sources": [low, high]}, ledger, max_sources=2, corpus_mode="mixed")

    assert [item["name"] for item in selected["selected"]] == ["low"]
    assert selected["skipped"][0]["fingerprint"] == fingerprint


def test_record_training_batch_and_sync_status(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(json.dumps({"text": "def add(a,b): return a+b"}) + "\n", encoding="utf-8")
    source = _source("repo", 50)

    ledger = record_training_batch(
        tmp_path / "ledger.json",
        selected_sources=[{**source, "training_fingerprint": source_fingerprint(source, corpus_mode="mixed")}],
        dataset_path=dataset,
        dataset={"records": 1, "bytes": dataset.stat().st_size},
        job={"job": {"id": "train_1", "status": "queued"}},
        ingest={"ok": True, "records": 1, "bytes": dataset.stat().st_size, "languages": ["Python"], "corpus_mode": "mixed"},
        corpus_mode="mixed",
    )
    assert ledger["batches"]
    assert list(ledger["sources"].values())[0]["status"] == "queued"

    sync = sync_ledger_with_jobs(tmp_path / "ledger.json", [{"id": "train_1", "status": "done"}])

    assert sync["changed"] == 1
    after = load_ledger(tmp_path / "ledger.json")
    assert list(after["sources"].values())[0]["status"] == "done"
    assert list(after["batches"].values())[0]["status"] == "done"
