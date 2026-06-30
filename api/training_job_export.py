from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.storage import SchedulerStore

TRAINING_JOB_SCHEMA = "ailovanta.training_job.v1"
TRAINING_JOB_TYPES = {"rag_import", "lora_micro", "evaluation_batch", "private_memory_tune"}


def export_training_job(
    job_id: str,
    output_dir: str | Path = "runtime_data/training_exports",
    store: SchedulerStore | None = None,
) -> dict[str, Any]:
    scheduler = store or SchedulerStore()
    job = scheduler.get_job(job_id)
    if not job:
        raise ValueError("training job not found")

    job_type = str(job.get("job_type") or "")
    if job_type not in TRAINING_JOB_TYPES:
        raise ValueError("job is not a supported training job")

    payload = json.loads(job.get("payload_json") or "{}")
    exported = dict(payload)
    exported["schema_version"] = TRAINING_JOB_SCHEMA
    exported["job_id"] = job_id
    exported["kind"] = job_type

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{job_id}.json"
    file_path.write_text(json.dumps(exported, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"job_id": job_id, "export_path": str(file_path), "payload": exported}
