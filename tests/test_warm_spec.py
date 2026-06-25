from api.model_warm import WarmSpec


def test_defaults() -> None:
    item = WarmSpec()
    assert item.model_key.endswith(":candidate")
    assert item.runtime_id
    assert item.node_id
