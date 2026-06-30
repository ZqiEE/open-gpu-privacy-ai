from __future__ import annotations

import json
from pathlib import Path

from api.autonomous_code_training_loop import AutonomousCodeTrainingLoop, candidate_files_for_record, extract_backend_ref_from_pipeline


def make_repo(root: Path) -> None:
    (root / "README.md").write_text("Ailovanta arithmetic package. Use add(left, right) for deterministic integer sums.", encoding="utf-8")
    (root / "app.py").write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "from app import add\n\n\ndef test_add_contract():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0\n",
        encoding="utf-8",
    )


def make_failing_repo(root: Path) -> None:
    (root / "app.py").write_text("def add(left, right):\n    return left - right\n", encoding="utf-8")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "\n".join(
            [
                "from app import add",
                "",
                "",
                "def test_add_contract():",
                "    # The public arithmetic helper must return deterministic integer sums.",
                "    assert add(2, 3) == 5",
                "    assert add(-1, 1) == 0",
                "    assert add(100, 25) == 125",
            ]
        ),
        encoding="utf-8",
    )


def test_candidate_files_for_record_includes_repo_implementation(tmp_path: Path) -> None:
    make_repo(tmp_path)
    record = {"source_root": str(tmp_path), "path": "tests/test_app.py"}
    candidates = candidate_files_for_record(record)
    assert "app.py" in candidates
    assert "tests/test_app.py" not in candidates


def test_autonomous_code_training_loop_reaches_verified_samples(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    make_repo(repo)
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "local_repo",
                        "path": str(repo),
                        "license_policy": "private_owner_unrestricted",
                        "enabled": True,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = AutonomousCodeTrainingLoop(core_path=tmp_path / "missing-core", root=tmp_path / "loop").run_once(
        sources_path=sources,
        fetch=False,
        max_tasks=5,
        run_foundation=False,
    )

    assert result["ok"] is True
    assert result["stage"] == "verified_samples_ready"
    assert result["task_results"]["passed"] >= 1
    assert result["verified"]["count"] >= 1
    assert result["failures"]["count"] == 0


def test_autonomous_code_training_loop_exports_failed_samples_when_repair_disabled(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    make_failing_repo(repo)
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "local_repo",
                        "path": str(repo),
                        "license_policy": "private_owner_unrestricted",
                        "enabled": True,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = AutonomousCodeTrainingLoop(core_path=tmp_path / "missing-core", root=tmp_path / "loop").run_once(
        sources_path=sources,
        fetch=False,
        max_tasks=5,
        run_foundation=False,
        repair_failures=False,
    )

    assert result["ok"] is False
    assert result["stage"] == "no_verified_samples"
    assert result["verified"]["count"] == 0
    assert result["failures"]["count"] == 1
    assert result["repairs"]["repaired"] == 0


def test_autonomous_code_training_loop_repairs_failed_tasks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    make_failing_repo(repo)
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            {
                "schema_version": "ailovanta.github_code_sources.v1",
                "sources": [
                    {
                        "name": "local_repo",
                        "path": str(repo),
                        "license_policy": "private_owner_unrestricted",
                        "enabled": True,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = AutonomousCodeTrainingLoop(core_path=tmp_path / "missing-core", root=tmp_path / "loop").run_once(
        sources_path=sources,
        fetch=False,
        max_tasks=5,
        run_foundation=False,
        max_repair_candidates=8,
    )

    assert result["ok"] is True
    assert result["stage"] == "verified_samples_ready"
    assert result["task_results"]["failed"] == 1
    assert result["failures"]["count"] == 1
    assert result["repairs"]["repaired"] == 1
    assert result["verified"]["count"] == 1


def test_extract_backend_ref_from_pipeline_result_path(tmp_path: Path) -> None:
    result_path = tmp_path / "foundation_result.json"
    result_path.write_text(
        json.dumps(
            {
                "artifact": {
                    "backend_ref": "file:///tmp/checkpoint.bin",
                    "checkpoint_uri": "artifact://fallback",
                }
            }
        ),
        encoding="utf-8",
    )
    foundation = {"pipeline": {"result_path": str(result_path)}}

    assert extract_backend_ref_from_pipeline(foundation) == "file:///tmp/checkpoint.bin"
    assert foundation["pipeline"]["foundation_result"]["artifact"]["backend_ref"] == "file:///tmp/checkpoint.bin"


def test_autonomous_loop_persists_and_reuses_latest_backend_ref(tmp_path: Path) -> None:
    loop = AutonomousCodeTrainingLoop(core_path=tmp_path / "missing-core", root=tmp_path / "loop")
    saved = loop._write_latest_backend_ref(
        "file:///tmp/model-or-checkpoint",
        run_id="auto_code_prev",
        foundation={"pipeline": {"result_path": "runtime_data/foundation_result.json"}},
    )

    resolved = loop._resolve_repair_backend_ref(None)

    assert saved["schema_version"] == "ailovanta.autonomous_code_latest_backend_ref.v1"
    assert resolved["backend_ref"] == "file:///tmp/model-or-checkpoint"
    assert resolved["source"] == "latest_foundation_artifact"


def test_autonomous_loop_explicit_backend_ref_overrides_latest(tmp_path: Path) -> None:
    loop = AutonomousCodeTrainingLoop(core_path=tmp_path / "missing-core", root=tmp_path / "loop")
    loop._write_latest_backend_ref("file:///tmp/old", run_id="old", foundation={"pipeline": {}})

    resolved = loop._resolve_repair_backend_ref("file:///tmp/new")

    assert resolved == {"backend_ref": "file:///tmp/new", "source": "explicit"}
