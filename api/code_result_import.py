from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from api.runtime_router import ModelManifest
from api.runtime_store import RuntimeStore

DEFAULT_CODE_RESULTS_PATH = Path("runtime_data/code_results.json")


class CoreCodeResultError(ValueError):
    pass


class CoreCodeResultImporter:
    def __init__(self, path: str | Path = DEFAULT_CODE_RESULTS_PATH, runtime_store: RuntimeStore | None = None) -> None:
        self.path = Path(path)
        self.runtime_store = runtime_store or RuntimeStore()

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(item) for item in payload]
        return list(payload.get("results") or [])

    def _write_all(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_result(self, manifest: dict[str, Any]) -> dict[str, Any]:
        if manifest.get("schema_version") != "ailovanta.core_code_result.v1":
            raise CoreCodeResultError("invalid schema_version")
        if not manifest.get("next_model_version"):
            raise CoreCodeResultError("next_model_version is required")

        items = self._read_all()
        items.append(manifest)
        self._write_all(items)

        version = str(manifest["next_model_version"])
        digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()
        runtime_model = self.runtime_store.register_model(
            ModelManifest(
                model_id="ailovanta-code",
                version=version,
                manifest_hash="sha256:" + digest,
                privacy_level="public",
                min_gpu_memory_gb=0.0,
                allowed_pools=("small_gpu_pool", "large_gpu_pool", "enterprise_pool"),
                quantization="adapter-candidate",
                context_length=8192,
                adapter_compatible=True,
                status="candidate",
            )
        )
        return {"ok": True, "result": manifest, "runtime_model": runtime_model}

    def list_results(self) -> list[dict[str, Any]]:
        return self._read_all()
