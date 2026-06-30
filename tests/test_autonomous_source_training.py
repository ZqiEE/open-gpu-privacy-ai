import json
from pathlib import Path

from api.autonomous_source_training import corpus_to_training_dataset, run_autonomous_source_training_cycle, training_text_from_record


def test_training_text_from_instruction_record() -> None:
    text = training_text_from_record(
        {
            "training_record_kind": "instruction",
            "instruction": "Explain setup",
            "context": "Install dependencies and run tests.",
            "expected_response": "Give actionable setup steps.",
        }
    )

    assert "Instruction: Explain setup" in text
    assert "Context: Install dependencies" in text
    assert "Expected: Give actionable" in text


def test_corpus_to_training_dataset(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        json.dumps(
            {
                "training_record_kind": "code",
                "text": "def add(a, b): return a + b",
                "path": "src/add.py",
                "source_name": "local",
                "rights_id": "rights_1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = corpus_to_training_dataset(corpus, tmp_path / "train.jsonl")

    assert result["ok"] is True
    assert result["records"] == 1
    assert "def add" in (tmp_path / "train.jsonl").read_text(encoding="utf-8")


def test_autonomous_source_training_cycle_queues_job(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "README.md").write_text("Ailovanta local source explains autonomous training setup and worker execution." * 3, encoding="utf-8")
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "local-source",
                        "path": str(repo),
                        "license_policy": "owner_controlled",
                        "enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    posted = {}

    def fake_post(server: str, path: str, body: dict):
        posted["server"] = server
        posted["path"] = path
        posted["body"] = body
        return {"ok": True, "job": {"id": "train_auto_1", "status": "queued", "payload": body}}

    monkeypatch.setattr("api.autonomous_source_training.post_json", fake_post)

    result = run_autonomous_source_training_cycle(
        server="http://127.0.0.1:8000",
        sources_path=sources,
        work_root=tmp_path / "work",
        discover=False,
        fetch=False,
        max_sources=5,
        max_records=10,
        corpus_mode="mixed",
    )

    assert result["ok"] is True
    assert result["stage"] == "training_job_queued"
    assert result["dataset"]["records"] > 0
    assert posted["path"] == "/training/jobs"
    assert posted["body"]["kind"] == "lora_micro"
    assert posted["body"]["dataset_uri"].startswith("file://")
