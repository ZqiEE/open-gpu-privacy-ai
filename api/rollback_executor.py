from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.model_monitor import ModelMonitorStore
from api.runtime_store import RuntimeStore


class RollbackExecutor:
    def __init__(
        self,
        monitor: ModelMonitorStore | None = None,
        runtime: RuntimeStore | None = None,
        log_root: str | Path = "runtime_data/rollback_executor",
    ) -> None:
        self.monitor = monitor or ModelMonitorStore()
        self.runtime = runtime or RuntimeStore()
        self.log_root = Path(log_root)
        self.log_root.mkdir(parents=True, exist_ok=True)

    def execute_latest(self) -> dict[str, Any]:
        actions = self.monitor.list_actions()
        rollback_actions = [item for item in actions if item.get("action") == "rollback"]
        if not rollback_actions:
            return self._log({"executed": False, "reason": "no_rollback_action"})
        action = sorted(rollback_actions, key=lambda item: item.get("created_at", 0), reverse=True)[0]
        return self.execute_action(action)

    def execute_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if action.get("action") != "rollback":
            return self._log({"executed": False, "reason": "not_a_rollback_action", "action": action})
        bad_model = action.get("model")
        if not bad_model:
            return self._log({"executed": False, "reason": "missing_model", "action": action})

        live_record = self._find_live_by_model(bad_model)
        previous_model = live_record.get("previous_model") if live_record else None
        bad_update = self._set_model_status(bad_model, "rolled_back")
        previous_update = self._set_model_status(previous_model, "active") if previous_model else None
        payload = {
            "executed": True,
            "rollback_id": "rollback_" + uuid4().hex[:12],
            "action_id": action.get("action_id"),
            "bad_model": bad_model,
            "previous_model": previous_model,
            "bad_update": bad_update,
            "previous_update": previous_update,
            "created_at": round(time(), 3),
        }
        return self._log(payload)

    def _find_live_by_model(self, model: str) -> dict[str, Any] | None:
        rows = self.monitor.list_live()
        rows = [row for row in rows if row.get("model") == model]
        rows.sort(key=lambda row: row.get("created_at", 0), reverse=True)
        return rows[0] if rows else None

    def _set_model_status(self, model_key: str | None, status: str) -> dict[str, Any] | None:
        if not model_key:
            return None
        with self.runtime.connect() as conn:
            before = conn.execute("SELECT status FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
            conn.execute("UPDATE runtime_models SET status = ? WHERE model_key = ?", (status, model_key))
            after = conn.execute("SELECT status FROM runtime_models WHERE model_key = ?", (model_key,)).fetchone()
        return {
            "model_key": model_key,
            "before": before[0] if before else None,
            "after": after[0] if after else None,
            "found": after is not None,
        }

    def _log(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = {**payload, "log_id": payload.get("rollback_id") or "rollback_log_" + uuid4().hex[:12], "logged_at": round(time(), 3)}
        path = self.log_root / f"{payload['log_id']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def list_logs(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.log_root.glob("*.json"))]
