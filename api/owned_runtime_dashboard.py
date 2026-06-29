from __future__ import annotations

from typing import Any

from api.reputation_ops import ReputationOps
from api.runtime_store import RuntimeStore
from api.worker_result_validator import WorkerResultValidationStore


class OwnedRuntimeDashboard:
    def __init__(
        self,
        runtime_store: RuntimeStore,
        validation_store: WorkerResultValidationStore,
        reputation_store: ReputationOps,
    ) -> None:
        self.runtime_store = runtime_store
        self.validation_store = validation_store
        self.reputation_store = reputation_store

    def summary(self, limit: int = 20) -> dict[str, Any]:
        runtime_status = self.runtime_store.status()
        assignments = self.runtime_store.list_assignments(limit=limit)
        validations = self.validation_store.list(limit=limit)
        node_ids = sorted({str(item.get("node_id")) for item in validations if item.get("node_id")})
        reputation_events = self._recent_reputation_events(node_ids, limit=limit)
        failed_validations = [item for item in validations if not item.get("passed")]
        passed_count = len([item for item in validations if item.get("passed")])
        pass_rate = round(passed_count / len(validations), 3) if validations else 0.0
        recent_successful_route = next((item for item in assignments if item.get("assigned")), None)
        blockers = self._blockers(runtime_status, assignments, validations)

        return {
            "ok": not blockers,
            "blockers": blockers,
            "runtime": runtime_status,
            "route": {
                "recent_assignments": assignments,
                "recent_successful_assignment": recent_successful_route,
                "recent_assignment_count": len(assignments),
            },
            "worker_validation": {
                "recent_receipts": validations,
                "recent_receipt_count": len(validations),
                "passed_recent": passed_count,
                "failed_recent": len(failed_validations),
                "pass_rate": pass_rate,
                "latest_receipt": validations[0] if validations else None,
            },
            "reputation": {
                "events": reputation_events,
                "event_count": len(reputation_events),
            },
        }

    def _recent_reputation_events(self, node_ids: list[str], limit: int) -> list[dict[str, Any]]:
        if not node_ids:
            return self.reputation_store.list_events(limit=limit)
        events: list[dict[str, Any]] = []
        for node_id in node_ids:
            events.extend(self.reputation_store.list_events(node_id=node_id, limit=limit))
        events.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return events[:limit]

    @staticmethod
    def _blockers(runtime_status: dict[str, Any], assignments: list[dict[str, Any]], validations: list[dict[str, Any]]) -> list[str]:
        blockers: list[str] = []
        if int(runtime_status.get("models") or 0) <= 0:
            blockers.append("runtime_model_missing")
        if int(runtime_status.get("online_runtimes") or 0) <= 0:
            blockers.append("online_runtime_missing")
        if assignments and not any(item.get("assigned") for item in assignments):
            blockers.append("recent_runtime_route_failed")
        if not validations:
            blockers.append("worker_validation_receipt_missing")
        elif not validations[0].get("passed"):
            blockers.append("latest_worker_validation_failed")
        return blockers
