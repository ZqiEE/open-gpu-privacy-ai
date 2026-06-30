import json
from pathlib import Path

from api.training_code_eval import evaluate_training_code_dataset


def test_training_code_eval_accepts_python_code_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(json.dumps({"text": "def add(a, b):\n    return a + b\n", "record_kind": "code", "source_path": "app.py"}) + "\n", encoding="utf-8")

    result = evaluate_training_code_dataset(dataset)

    assert result["ok"] is True
    assert result["code_records"] == 1
    assert result["syntax_checks"] == 1
    assert result["syntax_failed"] == 0


def test_training_code_eval_blocks_plain_text_dataset(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(json.dumps({"text": "plain product notes"}) + "\n", encoding="utf-8")

    result = evaluate_training_code_dataset(dataset)

    assert result["ok"] is False
    assert "no_code_records" in result["blockers"]
    assert "no_syntax_checks" in result["blockers"]


def test_training_code_eval_blocks_invalid_python(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(json.dumps({"text": "def broken(:\n    pass\n", "record_kind": "code", "source_path": "broken.py"}) + "\n", encoding="utf-8")

    result = evaluate_training_code_dataset(dataset)

    assert result["ok"] is False
    assert "syntax_failed" in result["blockers"]
