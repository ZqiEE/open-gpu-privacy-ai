import json
from pathlib import Path

from api.github_code_ingest import ingest_sources, source_allowed


def test_authorized_unrestricted_source_allows_unknown_license() -> None:
    ok, reason = source_allowed({"license_policy": "private_owner_unrestricted", "license_hint": "unknown"})
    assert ok is True
    assert reason == "authorized:private_owner_unrestricted"


def test_public_safe_source_blocks_unknown_license() -> None:
    ok, reason = source_allowed({"license_policy": "public_safe", "license_hint": "unknown"})
    assert ok is False
    assert reason == "public_safe:unknown"


def test_ingest_authorized_code_builds_corpus_rights_and_training_job(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text(
        "\n".join(
            [
                "# Demo API",
                "",
                "This repository exposes an add(left, right) helper.",
                "Implementations must keep integer addition deterministic and easy to test.",
                "The public function should return the sum of both arguments without side effects.",
            ]
        ),
        encoding="utf-8",
    )
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "\n".join(
            [
                "from app import add",
                "",
                "",
                "def test_add_returns_sum():",
                "    assert add(2, 3) == 5",
                "    assert add(-1, 1) == 0",
            ]
        ),
        encoding="utf-8",
    )
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "owned-repo",
                        "path": str(repo),
                        "license_policy": "private_owner_unrestricted",
                        "license_hint": "unknown",
                        "enabled": True,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = ingest_sources(
        sources,
        corpus_output=tmp_path / "corpus.jsonl",
        rights_path=tmp_path / "rights.json",
        jobs_path=tmp_path / "jobs.json",
        fetch=False,
        create_job=True,
    )

    assert result["ok"] is True
    assert result["corpus_mode"] == "instructions"
    assert result["records"] == 2
    assert result["created_jobs"][0]["distributed_required"] is True
    corpus_line = json.loads((tmp_path / "corpus.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert corpus_line["training_record_kind"] == "instruction"
    assert "instruction" in corpus_line
    assert "expected_response" in corpus_line
    assert corpus_line["rights_id"].startswith("rights_code_")
    assert corpus_line["authorization_basis"] == "authorized:private_owner_unrestricted"
    rights = json.loads((tmp_path / "rights.json").read_text(encoding="utf-8"))
    assert rights[0]["commercial_use_allowed"] is True
    assert rights[0]["distillation_allowed"] is True


def test_ingest_can_build_raw_code_corpus_when_requested(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text(
        "\n".join(
            [
                "def add(left: int, right: int) -> int:",
                "    return left + right",
                "",
                "def describe() -> str:",
                "    return 'authorized training sample'",
            ]
        ),
        encoding="utf-8",
    )
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [{"name": "owned-repo", "path": str(repo), "license_policy": "authorized_unrestricted", "enabled": True}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = ingest_sources(sources, corpus_output=tmp_path / "code.jsonl", rights_path=tmp_path / "rights.json", jobs_path=tmp_path / "jobs.json", fetch=False, corpus_mode="code")

    assert result["ok"] is True
    assert result["corpus_mode"] == "code"
    line = json.loads((tmp_path / "code.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert line["training_record_kind"] == "code"
    assert line["language"] == "python"
