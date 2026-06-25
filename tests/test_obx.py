from api.outbox_api import router
from api.outbox_run import run_from_payload


def test_outbox_api_paths() -> None:
    paths = [route.path for route in router.routes]
    assert "/outbox/submit" in paths
    assert "/outbox/runs" in paths


def test_no_flow_without_flag() -> None:
    assert run_from_payload({"id": "x", "plan_path": "p.json"}) is None
