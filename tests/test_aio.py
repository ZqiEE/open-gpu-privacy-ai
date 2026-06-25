from scripts.aio import call


def test_aio_call_returns_payload() -> None:
    result = call(["-c", "import json; print(json.dumps({'ok': True}))"])
    assert result["ok"] is True
    assert result["returncode"] == 0
