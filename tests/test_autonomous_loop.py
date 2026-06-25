from pathlib import Path

from api.autonomous_loop import AutonomousLoop


def test_autonomous_loop_run_records(tmp_path: Path) -> None:
    loop = AutonomousLoop(core_path=tmp_path, root=tmp_path / "loop")
    payload = {"run_id": "auto_test", "ok": True, "created_at": 1.0}
    loop._write_run(payload)
    assert loop.latest_run()["run_id"] == "auto_test"
    assert loop.list_runs()[0]["ok"] is True
