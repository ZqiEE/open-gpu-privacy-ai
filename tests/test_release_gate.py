from api.release_gate import release_gate


def test_release_gate_shape() -> None:
    result = release_gate(core_path=".", run_tests=False)
    assert result["stage"] in {"release_pass", "release_blocked"}
    assert "checks" in result
    assert "blockers" in result
