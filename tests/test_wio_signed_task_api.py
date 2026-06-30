import json

from fastapi.testclient import TestClient

from api.main_learning import app
from api.node_trust import NodeTrustStore
from api.parcel_store import ParcelStore
from api.wio import signed_result


def test_signed_task_claim_and_result_binding(tmp_path, monkeypatch) -> None:
    import api.wio_api as wio_api

    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_NODE_SECRETS_JSON", json.dumps({"node-1": "secret"}))
    NodeTrustStore().register("node-1", "secret", trust_score=0.9)
    original_store = wio_api.store
    wio_api.store = ParcelStore(tmp_path / "parcels")
    try:
        client = TestClient(app)
        created = client.post(
            "/wio/task",
            json={
                "plan": {"plan_id": "p1", "max_steps": 1, "estimated_total_tokens": 10},
                "node_id": "node-1",
                "input_uri": "file://input.jsonl",
                "output_uri": "file://out",
            },
        )
        assert created.status_code == 200
        task = created.json()["item"]["task"]

        claimed = client.post(f"/wio/tasks/{task['task_id']}/claim", params={"node_id": "node-1"})
        assert claimed.status_code == 200
        assert claimed.json()["task_check"]["ok"] is True

        payload = signed_result(
            {
                "task_id": task["task_id"],
                "checkpoint_uri": "file://checkpoint.bin",
                "checkpoint_hash": "sha256:abc",
                "token_count": 10,
                "train_loss": 0.1,
                "eval_loss": 0.2,
            },
            node_id="node-1",
            secret="secret",
        )
        submitted = client.post("/wio/result", json={"payload": payload})
        assert submitted.status_code == 200
        assert submitted.json()["checked"]["task"]["ok"] is True
    finally:
        wio_api.store = original_store


def test_result_for_wrong_node_is_rejected(tmp_path, monkeypatch) -> None:
    import api.wio_api as wio_api

    monkeypatch.setenv("AILOVANTA_NODE_TRUST_PATH", str(tmp_path / "trust.sqlite3"))
    monkeypatch.setenv("AILOVANTA_NODE_SECRETS_JSON", json.dumps({"node-2": "secret"}))
    NodeTrustStore().register("node-2", "secret", trust_score=0.9)
    original_store = wio_api.store
    wio_api.store = ParcelStore(tmp_path / "parcels")
    try:
        client = TestClient(app)
        task = client.post(
            "/wio/task",
            json={
                "plan": {"plan_id": "p1"},
                "node_id": "node-1",
                "input_uri": "file://input.jsonl",
                "output_uri": "file://out",
            },
        ).json()["item"]["task"]
        payload = signed_result(
            {
                "task_id": task["task_id"],
                "checkpoint_uri": "file://checkpoint.bin",
                "checkpoint_hash": "sha256:abc",
            },
            node_id="node-2",
            secret="secret",
        )
        submitted = client.post("/wio/result", json={"payload": payload})
        assert submitted.status_code == 400
        assert submitted.json()["detail"]["reason"] == "node_id_mismatch"
    finally:
        wio_api.store = original_store
