from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.foundation_job_store import FOUNDATION_JOB_SCHEMA, FoundationJobStore


def export_foundation_job(job_id: str, output_dir: str | Path = "runtime_data/foundation_exports", store: FoundationJobStore | None = None) -> dict[str, Any]:
    job_store = store or FoundationJobStore()
    job = job_store.get(job_id)
    if not job:
        raise ValueError("foundation job not found")

    payload = dict(job["payload"])
    payload["schema_version"] = FOUNDATION_JOB_SCHEMA
    payload["job_id"] = job_id

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{job_id}.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"job_id": job_id, "export_path": str(file_path), "payload": payload}
