from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Show latest foundation result summary")
    parser.add_argument("--root", default="runtime_data/guarded_learning_pipeline")
    args = parser.parse_args()
    paths = sorted((Path(args.root) / "results").glob("*_foundation_result.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not paths:
        print(json.dumps({"ok": False, "reason": "no result"}, ensure_ascii=False, indent=2))
        return 1
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    artifact = data.get("artifact") or {}
    print(json.dumps({"ok": True, "path": str(paths[0]), "artifact_id": artifact.get("artifact_id"), "model_id": artifact.get("model_id"), "version": artifact.get("version"), "backend_ref": artifact.get("backend_ref") or artifact.get("checkpoint_uri")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
