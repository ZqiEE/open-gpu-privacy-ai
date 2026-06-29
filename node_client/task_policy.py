from __future__ import annotations

import json
from dataclasses import dataclass


ALLOWED_JOB_TYPES = {
    "rag_index",
    "rag_import",
    "evaluation",
    "evaluation_batch",
    "verification",
    "lora_micro",
    "model_shard",
    "code_instruction_eval",
}


@dataclass(frozen=True)
class TaskPolicy:
    allowed_job_types: set[str]
    max_payload_bytes: int = 16_384
    max_runtime_seconds: float = 10.0

    @classmethod
    def default(cls) -> "TaskPolicy":
        return cls(allowed_job_types=set(ALLOWED_JOB_TYPES))

    def validate(self, job: dict) -> tuple[bool, str]:
        job_type = job.get("type") or job.get("job_type") or "unknown"
        if job_type not in self.allowed_job_types:
            return False, f"job type not allowed: {job_type}"
        payload = job.get("payload", {})
        payload_size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        if payload_size > self.max_payload_bytes:
            return False, f"payload too large: {payload_size} bytes"
        return True, "accepted"
