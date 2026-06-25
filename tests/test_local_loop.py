from pathlib import Path

from scripts.local_loop import sha, write_plan


def test_sha() -> None:
    assert sha("x").startswith("sha256:")


def test_write_plan(tmp_path: Path) -> None:
    plan = write_plan(tmp_path / "plan.json")
    assert plan["schema_version"] == "ailovanta.foundation_plan.v1"
    assert plan["model"]["model_id"] == "ailovanta-owned"
