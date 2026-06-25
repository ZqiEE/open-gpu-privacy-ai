from pathlib import Path

from api.autotruth_store import AutoTruthEventStore


def test_autotruth_event_store_round_trip(tmp_path: Path) -> None:
    store = AutoTruthEventStore(tmp_path / "learning")
    event = store.add_event({"input": "hello", "output": "world", "behavior": {"copy": 1}})
    assert event["event_id"].startswith("evt_")
    exported = store.export_events(tmp_path / "events.json")
    assert exported["event_count"] == 1
    run = store.import_run({"rows": [], "training_pack": {"pack_id": "pack_1", "sft": []}})
    assert run["pack_id"] == "pack_1"
    assert store.latest_pack()["pack_id"] == "pack_1"
