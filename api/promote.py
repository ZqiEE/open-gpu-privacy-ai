from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY = Path("runtime_data/model_registry.json")


def load(path: str | Path, default: Any) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save(path: str | Path, data: Any) -> Any:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def newest(root: str | Path = "runtime_data/manifests") -> Path | None:
    folder = Path(root)
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def gate(manifest: str | Path | None = None, eval_file: str | Path = "runtime_data/code_eval.json", min_score: float = 1.0) -> dict[str, Any]:
    mp = Path(manifest) if manifest else newest()
    if not mp or not mp.exists():
        return {"ok": False, "reason": "manifest_not_found"}
    m = load(mp, {})
    ev = load(eval_file, {"score": 0, "failed": 999})
    score = float(ev.get("score") or 0)
    failed = int(ev.get("failed") or 0)
    if score < min_score or failed > 0:
        return {"ok": False, "reason": "eval_not_passed", "score": score, "failed": failed, "required_score": min_score}
    reg = load(REGISTRY, {"schema_version": "ailovanta.model_registry.v1", "models": []})
    rec = {
        "model_id": str(m.get("artifact_name", "ailovanta-model")).split("-")[0],
        "artifact_name": m.get("artifact_name"),
        "artifact_hash": m.get("artifact_hash"),
        "manifest_ref": "file://" + str(mp.resolve()),
        "chunk_count": m.get("chunk_count"),
        "artifact_bytes": m.get("artifact_bytes"),
        "eval_score": score,
        "eval_failed": failed,
        "status": "promoted",
    }
    reg["models"] = [x for x in reg.get("models", []) if x.get("artifact_hash") != rec["artifact_hash"]]
    reg["models"].append(rec)
    save(REGISTRY, reg)
    return {"ok": True, "model": rec, "registry": str(REGISTRY)}
