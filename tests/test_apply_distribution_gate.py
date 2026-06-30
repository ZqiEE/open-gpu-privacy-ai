import json
from pathlib import Path

from api.ra2 import apply2
from api.route_book import RouteBook


def _foundation_result(tmp_path: Path) -> Path:
    checkpoint = tmp_path / "checkpoint.bin"
    checkpoint.write_bytes(b"owned-checkpoint")
    payload = {
        "plan": {"plan_id": "plan_1", "model": {"model_id": "ailovanta-owned"}},
        "artifact": {
            "artifact_id": "artifact_1",
            "artifact_hash": "sha256:model-artifact-record",
            "model_id": "ailovanta-owned",
            "version": "candidate",
            "source_plan_id": "plan_1",
            "checkpoint_uri": "file://" + str(checkpoint),
            "backend_kind": "checkpoint-artifact",
            "backend_ref": "file://" + str(checkpoint),
            "metrics": {"proof_coverage": 1.0, "avg_trust_score": 1.0},
        },
    }
    result_path = tmp_path / "foundation_result.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return result_path


def test_apply2_publishes_route_when_distribution_gate_disabled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result_path = _foundation_result(tmp_path)

    result = apply2(result_path, verify_distribution=False)

    assert result["ok"] is True
    assert result["artifact_distribution"]["skipped"] is True
    assert RouteBook().active("owned-chat/default") is not None


def test_apply2_blocks_route_when_distribution_gate_fails(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result_path = _foundation_result(tmp_path)

    result = apply2(result_path, verify_distribution=True)

    assert result["ok"] is False
    assert result["route"] is None
    assert "replica_book_under_replicated" in result["artifact_distribution"]["blockers"]
    assert RouteBook().active("owned-chat/default") is None


def test_apply2_publishes_route_when_chain_gate_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result_path = _foundation_result(tmp_path)

    result = apply2(result_path, verify_chain=True)

    assert result["ok"] is True
    assert result["chain_anchor"]["ok"] is True
    assert result["chain_anchor"]["event"]["anchor_status"] == "anchored"
    assert RouteBook().active("owned-chat/default") is not None
