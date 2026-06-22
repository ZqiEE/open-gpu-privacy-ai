from __future__ import annotations


class DashboardService:
    def __init__(self, store) -> None:
        self.store = store

    def summary(self) -> dict:
        status = self.store.status()
        total_jobs = status["queued_jobs"] + status["assigned_jobs"] + status["done_jobs"] + status["failed_jobs"]
        completed = status["done_jobs"] + status["failed_jobs"]
        pass_rate = 0.0
        if status["verifications"]:
            pass_rate = round(status["passed_verifications"] / status["verifications"], 3)
        return {
            "nodes": status["nodes"],
            "total_jobs": total_jobs,
            "queued_jobs": status["queued_jobs"],
            "assigned_jobs": status["assigned_jobs"],
            "completed_jobs": completed,
            "failed_jobs": status["failed_jobs"],
            "verifications": status["verifications"],
            "verification_pass_rate": pass_rate,
            "model_versions": status["model_versions"],
            "store": status["store"],
        }

    def recent_jobs(self, limit: int = 20) -> dict:
        return {"jobs": self.store.list_jobs(limit=limit)}

    def model_versions(self, limit: int = 20) -> dict:
        return {"models": self.store.list_model_versions(limit=limit)}
