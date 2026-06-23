from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time

from api.content_addressing import hash_object


@dataclass(frozen=True)
class ExecutionWindow:
    window_id: str
    node_id: str
    package_hash: str
    task_id: str
    runtime_hash: str
    valid_until: float
    window_hash: str


def open_execution_window(node_id: str, package_hash: str, task_id: str, runtime_hash: str, seconds: int = 300) -> dict:
    valid_until = round(time() + seconds, 3)
    payload = {"node_id": node_id, "package_hash": package_hash, "task_id": task_id, "runtime_hash": runtime_hash, "valid_until": valid_until}
    window_hash = hash_object(payload)
    item = ExecutionWindow(
        window_id="window_" + window_hash[:16],
        node_id=node_id,
        package_hash=package_hash,
        task_id=task_id,
        runtime_hash=runtime_hash,
        valid_until=valid_until,
        window_hash=window_hash,
    )
    return asdict(item)


def window_is_active(item: dict) -> bool:
    return float(item.get("valid_until", 0)) > time()
