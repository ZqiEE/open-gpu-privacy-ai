from __future__ import annotations

import hashlib
import json
from pathlib import Path
from time import time
from typing import Any

from api.replica_book import BOOK, add_copy, status as replica_status, under_replicated

TASKS = Path("runtime_data/replica_repair_tasks.json")
SCHEMA = "ailovanta.replica_repair_tasks.v1"
TASK_TYPE = "storage_replica_repair"


def stable_task_id(artifact_hash: str, chunk_hash: str, target_node_id: str) -> str:
    raw = f"{artifact_hash}|{chunk_hash}|{target_node_id}".encode("utf-8")
    return "replica_repair_" + hashlib.sha256(raw).hexdigest()[:16]


class ReplicaRepairStore:
    def __init__(self, path: str | Path = TASKS, replica_book_path: str | Path = BOOK) -> None:
        self.path = Path(path)
        self.replica_book_path = Path(replica_book_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA, "tasks": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def plan_repairs(self, artifact_hash: str | None = None, target_nodes: list[str] | None = None, max_tasks: int | None = None) -> dict[str, Any]:
        data = self.load()
        tasks = data.setdefault("tasks", {})
        created: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        weak_chunks = under_replicated(self.replica_book_path, artifact_hash=artifact_hash)
        for chunk in weak_chunks:
            existing_nodes = {str(copy.get("node_id") or "") for copy in chunk.get("copies", [])}
            candidates = self._target_nodes(chunk, target_nodes)
            needed = int(chunk.get("missing_replicas") or 0)
            for target_node_id in candidates:
                if max_tasks is not None and len(created) >= max_tasks:
                    break
                if needed <= 0:
                    break
                if target_node_id in existing_nodes:
                    continue
                task_id = stable_task_id(chunk["artifact_hash"], chunk["chunk_hash"], target_node_id)
                existing = tasks.get(task_id)
                if existing and existing.get("status") in {"queued", "assigned", "done"}:
                    skipped.append({"task_id": task_id, "reason": "existing_" + str(existing.get("status"))})
                    continue
                task = self._task(task_id, chunk, target_node_id)
                tasks[task_id] = task
                created.append(task)
                existing_nodes.add(target_node_id)
                needed -= 1
            if max_tasks is not None and len(created) >= max_tasks:
                break
        self.save(data)
        return {
            "ok": True,
            "created_count": len(created),
            "skipped_count": len(skipped),
            "under_replicated_count": len(weak_chunks),
            "tasks": created,
            "skipped": skipped,
            "replica_status": replica_status(self.replica_book_path),
            "tasks_path": str(self.path),
            "replica_book_path": str(self.replica_book_path),
        }

    def list_tasks(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        tasks = list(self.load().get("tasks", {}).values())
        if status:
            tasks = [task for task in tasks if task.get("status") == status]
        tasks.sort(key=lambda task: float(task.get("updated_at") or task.get("created_at") or 0), reverse=True)
        return tasks[:limit]

    def get(self, task_id: str) -> dict[str, Any] | None:
        return self.load().get("tasks", {}).get(task_id)

    def assign(self, task_id: str, node_id: str) -> dict[str, Any]:
        data = self.load()
        task = data.get("tasks", {}).get(task_id)
        if not task:
            raise ValueError("replica repair task not found")
        if task.get("status") == "done":
            raise ValueError("replica repair task already done")
        task["status"] = "assigned"
        task["assigned_to"] = node_id
        task["updated_at"] = round(time(), 3)
        self.save(data)
        return task

    def complete(self, task_id: str, node_id: str | None = None, location: str | None = None) -> dict[str, Any]:
        data = self.load()
        task = data.get("tasks", {}).get(task_id)
        if not task:
            raise ValueError("replica repair task not found")
        payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
        target_node_id = node_id or str(payload.get("target_node_id") or task.get("assigned_to") or "")
        if not target_node_id:
            raise ValueError("target node id required")
        target_location = location or str(payload.get("target_location") or "")
        if not target_location:
            raise ValueError("target location required")
        book = add_copy(
            artifact_hash=str(payload.get("artifact_hash") or ""),
            chunk_hash=str(payload.get("chunk_hash") or ""),
            node_id=target_node_id,
            location=target_location,
            path=self.replica_book_path,
        )
        task["status"] = "done"
        task["completed_by"] = target_node_id
        task["completed_location"] = target_location
        task["updated_at"] = round(time(), 3)
        task["completed_at"] = task["updated_at"]
        self.save(data)
        return {"ok": True, "task": task, "replica_book": book, "replica_status": replica_status(self.replica_book_path)}

    @staticmethod
    def _target_nodes(chunk: dict[str, Any], target_nodes: list[str] | None) -> list[str]:
        if target_nodes:
            return [node for node in target_nodes if node]
        missing = int(chunk.get("missing_replicas") or 0)
        return [f"storage-repair-{index}" for index in range(1, missing + 1)]

    @staticmethod
    def _task(task_id: str, chunk: dict[str, Any], target_node_id: str) -> dict[str, Any]:
        source_locations = [copy.get("location") for copy in chunk.get("copies", []) if copy.get("status") == "available" and copy.get("location")]
        target_location = f"node://{target_node_id}/artifacts/{chunk['artifact_hash'].replace(':', '_')}/{chunk['chunk_hash'].replace(':', '_')}"
        now = round(time(), 3)
        return {
            "schema_version": "ailovanta.replica_repair_task.v1",
            "task_id": task_id,
            "task_type": TASK_TYPE,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "payload": {
                "artifact_hash": chunk["artifact_hash"],
                "artifact_id": chunk.get("artifact_id"),
                "manifest_hash": chunk.get("manifest_hash"),
                "chunk_hash": chunk["chunk_hash"],
                "chunk_index": chunk.get("chunk_index"),
                "bytes": chunk.get("bytes"),
                "min_replicas": chunk.get("min_replicas"),
                "available_replicas": chunk.get("available_replicas"),
                "source_locations": source_locations,
                "target_node_id": target_node_id,
                "target_location": target_location,
            },
        }
