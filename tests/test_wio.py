from api.wc import make_result, make_task
from api.wio import task_envelope, verify_task_envelope


def test_make_task() -> None:
    task = make_task({"plan_id": "p1", "max_steps": 2, "estimated_total_tokens": 10}, "n1", "in", "out")
    assert task["plan_id"] == "p1"
    assert task["node_id"] == "n1"


def test_make_result() -> None:
    result = make_result({"task_id": "t1", "node_id": "n1", "checkpoint_uri": "u", "checkpoint_hash": "h", "token_count": 1, "train_loss": 0.1, "eval_loss": 0.2})
    assert result["task_id"] == "t1"
    assert result["schema_version"] == "ailovanta.worker_result.v1"


def test_task_envelope() -> None:
    item = task_envelope({"plan_id": "p1"}, "n1", "in", "out")
    assert item["kind"] == "worker_task"
    assert item["task"]["task_proof"]["schema_version"] == "ailovanta.task_proof.v1"
    assert verify_task_envelope(item)["ok"] is True


def test_task_envelope_detects_tampering() -> None:
    item = task_envelope({"plan_id": "p1"}, "n1", "in", "out")
    item["task"]["node_id"] = "n2"
    checked = verify_task_envelope(item)
    assert checked["ok"] is False
    assert checked["reason"] == "task_hash_mismatch"
