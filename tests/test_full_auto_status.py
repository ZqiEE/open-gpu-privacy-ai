import json

from scripts.show_full_auto_status import main


def test_show_full_auto_status_outputs_json(capsys) -> None:
    assert main() == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["ok"] is True
    assert "gpu" in payload
    assert "scheduler" in payload
    assert "latest_owned_binding" in payload
    assert "latest_owned_candidate" in payload
    assert "replica_status" in payload
    assert "continuous_training" in payload
    assert "jobs" in payload
    assert "nodes" in payload
