from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.training_artifact_binding import bind_local_training_artifact


def main() -> int:
    models_root = ROOT / "runtime_data" / "models"
    candidates = sorted(models_root.glob("*/output.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for output_path in candidates:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        binding = bind_local_training_artifact(output)
        if binding:
            print(json.dumps({"ok": True, "output": str(output_path), "binding": binding}, ensure_ascii=False, indent=2))
            return 0
    print(json.dumps({"ok": False, "reason": "no bindable local training artifact found"}, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
