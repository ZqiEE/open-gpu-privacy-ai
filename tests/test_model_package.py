from __future__ import annotations

from api.model_package import build_model_package


def test_build_model_package_creates_hash() -> None:
    package = build_model_package("demo", "v1", "base", "adapter_hash", "data_hash", 0.8, "obj_ref", tags=["ai"])
    assert package["name"] == "demo"
    assert package["package_hash"]
    assert package["score"] == 0.8
    assert package["tags"] == ["ai"]
