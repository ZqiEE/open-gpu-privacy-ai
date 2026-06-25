from api.outbox_api import router
from api.outbox_run import run_from_payload


def test_outbox_routes_exist() -> None:
    paths = [route.path for route in router.routes]
    assert "/outbox/submit" in paths
    assert "/outbox/runs" in paths


def test_run_from_payload_disabled() -> None:
    assert run_from_payload({"id": "x"}) is None
