from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def art(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get("artifact") if isinstance(data.get("artifact"), dict) else {}


def val(a: dict[str, Any], name: str, default: float = 1.0) -> float:
    m = a.get("metrics") if isinstance(a.get("metrics"), dict) else {}
    if m.get(name) is not None:
        return float(m[name])
    s = a.get("checkpoint_set") if isinstance(a.get("checkpoint_set"), dict) else {}
    if s.get(name) is not None:
        return float(s[name])
    return default


def ok(path: str | Path, min_pc: float = 0.8, min_ts: float = 0.75) -> dict[str, Any]:
    a = art(path)
    pc = val(a, "proof_coverage", 1.0)
    ts = val(a, "avg_trust_score", 1.0)
    blockers = []
    if pc < min_pc:
        blockers.append("proof_coverage_below_threshold")
    if ts < min_ts:
        blockers.append("avg_trust_score_below_threshold")
    return {"ok": not blockers, "blockers": blockers, "proof_coverage": pc, "avg_trust_score": ts}
