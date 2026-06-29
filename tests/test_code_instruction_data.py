from pathlib import Path

from api.code_instruction_data import build_instruction_records


def test_build_instruction_records_from_docs_and_tests(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# API\n\nUse `add(left, right)` to return a deterministic integer sum for callers.",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "\n".join(
            [
                "from app import add",
                "",
                "",
                "def test_add_contract():",
                "    # The helper is part of the public arithmetic API and must remain deterministic.",
                "    assert add(1, 2) == 3",
                "    assert add(-1, 1) == 0",
                "    assert add(100, 25) == 125",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")

    records = build_instruction_records(tmp_path)

    assert len(records) == 2
    types = {record.record_type for record in records}
    assert types == {"documentation", "test_spec"}
    assert all(record.instruction for record in records)
    assert all(record.expected_response for record in records)


def test_instruction_records_skip_secret_text(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "This documentation accidentally includes api_key='abcdefghijklmnopqrstuvwxyz1234567890'.",
        encoding="utf-8",
    )

    records = build_instruction_records(tmp_path)

    assert records == []
