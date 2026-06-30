import json
from pathlib import Path

from api.candidate_failure_actions import action_summary, load_actions, mark_action_submitted, plan_failure_actions


def _binding(tmp_path: Path) -> dict:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(json.dumps({"text": "tiny"}) + "\n", encoding="utf-8")
    return {
        "binding_id": "binding_failed",
        "artifact_hash": "sha256:artifact",
        "metadata": {"source_job_id": "train_source"},
    }, dataset


def test_plan_failure_actions_creates_retrain_for_model_gate_failure(tmp_path: Path) -> None:
    binding, dataset = _binding(tmp_path)
    gate = {
        "ok": False,
        "blockers": ["insufficient_training_rows"],
        "model_eval": {"dataset_path": str(dataset), "base_model": "ailovanta-base"},
    }

    result = plan_failure_actions(binding, gate, action_path=tmp_path / "actions.json")

    assert result["actions"][0]["action_type"] == "training_retrain"
    request = result["actions"][0]["training_job_request"]
    assert request["kind"] == "lora_micro"
    assert request["dataset_uri"].startswith("file://")
    assert "insufficient_training_rows" in request["notes"]
    assert action_summary(tmp_path / "actions.json")["statuses"]["queued"] == 1


def test_plan_failure_actions_is_idempotent_and_marks_submitted(tmp_path: Path) -> None:
    binding, dataset = _binding(tmp_path)
    gate = {"ok": False, "blockers": ["train_loss_out_of_bounds"], "model_eval": {"dataset_path": str(dataset)}}

    first = plan_failure_actions(binding, gate, action_path=tmp_path / "actions.json")
    second = plan_failure_actions(binding, gate, action_path=tmp_path / "actions.json")
    action_id = first["actions"][0]["action_id"]

    assert second["actions"][0]["action_id"] == action_id
    marked = mark_action_submitted(action_id, {"ok": True, "job": {"id": "train_retry"}}, path=tmp_path / "actions.json")

    assert marked["status"] == "submitted"
    assert load_actions(tmp_path / "actions.json")["actions"][action_id]["submission"]["job"]["id"] == "train_retry"


def test_plan_failure_actions_does_not_retrain_replica_only_failure(tmp_path: Path) -> None:
    binding, _ = _binding(tmp_path)
    gate = {"ok": False, "blockers": ["artifact_distribution:replica_book_under_replicated"], "model_eval": {}}

    result = plan_failure_actions(binding, gate, action_path=tmp_path / "actions.json")

    assert result["actions"] == []
