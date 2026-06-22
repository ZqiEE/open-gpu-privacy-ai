from __future__ import annotations

import tempfile
from pathlib import Path

from api.distributed_model_registry import DistributedModelRegistry
from api.model_package import build_model_package


def test_distributed_model_registry_registers_and_selects_best() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        registry = DistributedModelRegistry(Path(tmp) / "models.sqlite3")
        low = build_model_package("demo-low", "v1", "base", "a1", "d1", 0.3, "obj1", tags=["rag"])
        high = build_model_package("demo-high", "v1", "base", "a2", "d2", 0.9, "obj2", tags=["rag"])
        registry.register(low)
        registry.register(high)
        best = registry.best_package(tag="rag")
        assert best is not None
        assert best["name"] == "demo-high"
        assert registry.summary()["packages"] == 2
