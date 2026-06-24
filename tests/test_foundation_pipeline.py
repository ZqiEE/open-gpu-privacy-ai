from pathlib import Path

from api.foundation_pipeline import run_foundation_pipeline


def test_pipeline_requires_core_path(tmp_path: Path) -> None:
    missing_core = tmp_path / "missing-core"
    try:
        run_foundation_pipeline("job_1", core_path=missing_core, work_dir=tmp_path / "work")
    except ValueError as exc:
        assert "ailovanta-core path not found" in str(exc)
    else:
        raise AssertionError("missing core path should fail")
