from __future__ import annotations

import tempfile
from pathlib import Path

from api.storage import SchedulerStore


def test_scheduler_skips_gpu_job_for_cpu_node() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        node = store.register_node({
            "node_id": "node_cpu_route",
            "device_name": "cpu-route",
            "cpu_threads": 8,
            "memory_gb": 16,
            "has_gpu": False,
            "gpu_name": None,
            "contribution_percent": 30,
        })
        store.enqueue_job("job_gpu_only", "lora_micro", {"requires_gpu": True, "priority": 100})
        store.enqueue_job("job_cpu_ok", "evaluation", {"priority": 10})
        job = store.next_job(node["node_id"])
        assert job is not None
        assert job["id"] != "job_gpu_only"


def test_scheduler_assigns_gpu_job_to_gpu_node() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        node = store.register_node({
            "node_id": "node_gpu_route",
            "device_name": "gpu-route",
            "cpu_threads": 16,
            "memory_gb": 32,
            "has_gpu": True,
            "gpu_name": "test-gpu",
            "contribution_percent": 30,
        })
        store.enqueue_job("job_gpu_route", "lora_micro", {"requires_gpu": True, "priority": 100})
        job = store.next_job(node["node_id"])
        assert job is not None
        assert job["id"] == "job_gpu_route"


def test_route_preview_explains_matches() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = SchedulerStore(Path(tmp) / "scheduler.sqlite3")
        node = store.register_node({
            "node_id": "node_preview",
            "device_name": "preview-node",
            "cpu_threads": 8,
            "memory_gb": 8,
            "has_gpu": False,
            "gpu_name": None,
            "contribution_percent": 30,
        })
        preview = store.queued_route_preview(node["node_id"])
        assert preview["ok"] is True
        assert "routes" in preview
