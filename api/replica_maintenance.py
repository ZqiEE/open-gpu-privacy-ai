from __future__ import annotations

import hashlib
from pathlib import Path
from time import sleep
from typing import Any

from api.replica_book import load as load_replica_book, status as replica_status
from api.replica_repair import ReplicaRepairStore


def run_replica_maintenance_once(
    *,
    tasks_path: str | Path = "runtime_data/replica_repair_tasks.json",
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    storage_root: str | Path = "runtime_data/storage_replicas",
    target_nodes: list[str] | None = None,
    max_tasks: int | None = None,
    complete_local: bool = True,
) -> dict[str, Any]:
    store = ReplicaRepairStore(path=tasks_path, replica_book_path=replica_book_path)
    planned = store.plan_repairs(target_nodes=target_nodes, max_tasks=max_tasks)
    completed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    if complete_local:
        for task in store.list_tasks(status="queued", limit=max_tasks or 100):
            outcome = _complete_local_repair(store, task, Path(replica_book_path), Path(storage_root))
            if outcome.get("ok"):
                completed.append(outcome)
            elif outcome.get("skipped"):
                skipped.append(outcome)
            else:
                failed.append(outcome)
    return {
        "ok": not failed,
        "planned": planned,
        "completed_count": len(completed),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "completed": completed,
        "skipped": skipped,
        "failed": failed,
        "replica_status": replica_status(replica_book_path),
    }


def run_replica_maintenance_loop(
    *,
    interval: int = 60,
    tasks_path: str | Path = "runtime_data/replica_repair_tasks.json",
    replica_book_path: str | Path = "runtime_data/replica_book.json",
    storage_root: str | Path = "runtime_data/storage_replicas",
    target_nodes: list[str] | None = None,
    max_tasks: int | None = None,
    complete_local: bool = True,
) -> None:
    while True:
        run_replica_maintenance_once(
            tasks_path=tasks_path,
            replica_book_path=replica_book_path,
            storage_root=storage_root,
            target_nodes=target_nodes,
            max_tasks=max_tasks,
            complete_local=complete_local,
        )
        sleep(interval)


def _complete_local_repair(store: ReplicaRepairStore, task: dict[str, Any], replica_book_path: Path, storage_root: Path) -> dict[str, Any]:
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    task_id = str(task.get("task_id") or "")
    try:
        target_node = str(payload.get("target_node_id") or "")
        if not _is_local_maintenance_target(target_node):
            return {"ok": False, "skipped": True, "task_id": task_id, "reason": "non_local_target", "target_node_id": target_node}
        source_file = _first_local_source(payload.get("source_locations"))
        if not source_file:
            return {"ok": False, "task_id": task_id, "reason": "no_local_source"}
        chunk_hash = str(payload.get("chunk_hash") or "")
        chunk_bytes = _read_chunk_bytes(replica_book_path, source_file, str(payload.get("artifact_hash") or ""), chunk_hash)
        if _sha256(chunk_bytes) != chunk_hash:
            return {"ok": False, "task_id": task_id, "reason": "chunk_hash_mismatch"}
        target = _target_chunk_path(storage_root, target_node, str(payload.get("artifact_hash") or ""), chunk_hash)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(chunk_bytes)
        completed = store.complete(task_id, node_id=target_node, location="file://" + str(target))
        return {"ok": True, "task_id": task_id, "target": str(target), "task": completed["task"]}
    except Exception as exc:  # pragma: no cover - defensive status for long-running maintenance.
        return {"ok": False, "task_id": task_id, "reason": type(exc).__name__, "message": str(exc)}


def _first_local_source(source_locations: Any) -> Path | None:
    if not isinstance(source_locations, list):
        return None
    for raw in source_locations:
        if not isinstance(raw, str) or not raw:
            continue
        candidate = raw.removeprefix("file://")
        if raw.startswith("file://") or "://" not in raw:
            path = Path(candidate)
            if path.exists() and path.is_file():
                return path
    return None


def _read_chunk_bytes(replica_book_path: Path, source_file: Path, artifact_hash: str, chunk_hash: str) -> bytes:
    book = load_replica_book(replica_book_path)
    artifact = book.get("artifacts", {}).get(artifact_hash)
    if not artifact:
        raise ValueError("artifact not found in replica book")
    chunks = artifact.get("chunks", {})
    rows = sorted(chunks.items(), key=lambda item: _chunk_index(item[1].get("index")))
    offset = 0
    for current_hash, chunk in rows:
        size = int(chunk.get("bytes") or 0)
        if current_hash == chunk_hash:
            with source_file.open("rb") as handle:
                handle.seek(offset)
                return handle.read(size)
        offset += size
    raise ValueError("chunk not found in replica book")


def _target_chunk_path(storage_root: Path, target_node: str, artifact_hash: str, chunk_hash: str) -> Path:
    safe_artifact = artifact_hash.replace(":", "_")
    safe_chunk = chunk_hash.replace(":", "_")
    return storage_root / target_node / safe_artifact / f"{safe_chunk}.chunk"


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _is_local_maintenance_target(target_node: str) -> bool:
    return target_node == "localhost" or target_node.startswith("local-") or target_node.startswith("storage-repair-")


def _chunk_index(value: Any) -> int:
    if isinstance(value, int):
        return value
    text = str(value or "0")
    if text.isdigit():
        return int(text)
    if "_" in text:
        suffix = text.rsplit("_", 1)[-1]
        if suffix.isdigit():
            return int(suffix)
    return 0
