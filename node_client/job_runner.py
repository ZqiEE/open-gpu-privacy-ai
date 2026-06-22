from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class JobRunResult:
    job_id: str
    status: str
    output_summary: str
    runtime_seconds: float


class JobRunner:
    """Small safe demo runner.

    v0.6 intentionally keeps job execution simulated. A real node should execute only
    signed, sandboxed, resource-limited tasks.
    """

    def run(self, job: dict) -> JobRunResult:
        start = time.time()
        job_type = job.get("type", "unknown")
        time.sleep(self._simulated_seconds(job_type))
        return JobRunResult(
            job_id=job["id"],
            status="ok",
            output_summary=f"simulated sandboxed result for {job_type}",
            runtime_seconds=round(time.time() - start, 3),
        )

    @staticmethod
    def _simulated_seconds(job_type: str) -> float:
        return {
            "rag_index": 0.5,
            "evaluation": 0.7,
            "lora_micro": 1.0,
        }.get(job_type, 0.6)
