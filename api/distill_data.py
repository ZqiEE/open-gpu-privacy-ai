from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from api.secret_filter import scan_text


@dataclass(frozen=True)
class DistillRecord:
    task: str
    prompt: str
    teacher: str
    language: str
    source: str
    score: float
    text: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)


def render_example(item: dict[str, Any]) -> DistillRecord | None:
    prompt = str(item.get("prompt") or item.get("instruction") or item.get("question") or "").strip()
    teacher = str(item.get("teacher") or item.get("answer") or item.get("completion") or item.get("output") or "").strip()
    if len(prompt) < 8 or len(teacher) < 8:
        return None
    joined = prompt + "\n" + teacher
    if not scan_text(joined).ok:
        return None
    language = str(item.get("language") or item.get("lang") or "text")
    task = str(item.get("task") or "code_distill")
    source = str(item.get("source") or item.get("teacher_model") or "manual_teacher")
    try:
        score = float(item.get("score", 1.0))
    except Exception:
        score = 1.0
    text = (
        "<|task|>\n"
        + task
        + "\n<|language|>\n"
        + language
        + "\n<|prompt|>\n"
        + prompt
        + "\n<|teacher_answer|>\n"
        + teacher
        + "\n<|end|>\n"
    )
    return DistillRecord(task=task, prompt=prompt, teacher=teacher, language=language, source=source, score=score, text=text)


def read_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def build_distill_records(input_path: str | Path, min_score: float = 0.0) -> list[DistillRecord]:
    out: list[DistillRecord] = []
    for item in read_jsonl(input_path):
        record = render_example(item)
        if not record:
            continue
        if record.score < min_score:
            continue
        out.append(record)
    return out


def write_distill_jsonl(records: list[DistillRecord], output: str | Path) -> dict[str, Any]:
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(record.to_json() + "\n")
    return {
        "schema_version": "ailovanta.distill_corpus.v1",
        "output": str(target),
        "records": len(records),
        "avg_score": round(sum(r.score for r in records) / max(len(records), 1), 4),
        "sources": sorted({r.source for r in records}),
        "languages": sorted({r.language for r in records}),
    }
