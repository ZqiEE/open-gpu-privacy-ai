from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


def merge_ckpts(plan: dict[str, Any], items: list[dict[str, Any]] | None = None, src_root: str | Path = "runtime_data/model_deltas", out_root: str | Path = "runtime_data/merged_models") -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise RuntimeError("torch is required") from exc

    plan_id = str(plan["plan_id"])
    files = find_files(plan_id, items or [], src_root)
    if not files:
        raise RuntimeError("no ckpt files found for plan " + plan_id)

    parts = []
    for path in files:
        obj = torch.load(path, map_location="cpu")
        if not isinstance(obj, dict) or "state_dict" not in obj:
            raise RuntimeError("bad ckpt file " + str(path))
        parts.append(obj)

    state: dict[str, Any] = {}
    keys = sorted(set().union(*(part["state_dict"].keys() for part in parts)))
    for key in keys:
        vals = [part["state_dict"][key].float() for part in parts if key in part["state_dict"]]
        if not vals:
            continue
        shape = tuple(vals[0].shape)
        if any(tuple(val.shape) != shape for val in vals):
            raise RuntimeError("shape mismatch " + key)
        state[key] = sum(vals) / len(vals)

    hidden = int(parts[0].get("hidden_size") or 64)
    result = {
        "schema_version": "ailovanta.merged_checkpoint.v1",
        "plan_id": plan_id,
        "model_id": plan.get("model_id"),
        "version": plan.get("version") or plan.get("target_version"),
        "stage": plan.get("stage"),
        "hidden_size": hidden,
        "part_count": len(parts),
        "state_dict": state,
    }
    out = Path(out_root)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{safe(str(result['model_id']))}-{safe(str(result['version']))}-{safe(plan_id)}.pt"
    torch.save(result, target)
    return {
        "schema_version": "ailovanta.merged_checkpoint.v1",
        "plan_id": plan_id,
        "model_id": result["model_id"],
        "version": result["version"],
        "part_count": len(parts),
        "checkpoint_ref": "file://" + str(target.resolve()),
        "checkpoint_hash": file_hash(target),
        "ready_for_chat": True,
    }


def find_files(plan_id: str, items: list[dict[str, Any]], root: str | Path) -> list[Path]:
    files: list[Path] = []
    for item in items:
        path = to_path(str(item.get("delta_ref") or item.get("ref") or item.get("checkpoint_ref") or ""))
        if path and path.exists() and path.is_file():
            files.append(path)
    folder = Path(root) / safe(plan_id)
    if folder.exists():
        files.extend(sorted(folder.glob("*.pt")))
    out: list[Path] = []
    seen: set[str] = set()
    for path in files:
        key = str(path.resolve())
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def to_path(value: str) -> Path | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme == "file":
        p = unquote(parsed.path or value.removeprefix("file://"))
        if len(p) >= 3 and p[0] == "/" and p[2] == ":":
            p = p[1:]
        return Path(p)
    if parsed.scheme == "":
        return Path(value)
    return None


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:120]
