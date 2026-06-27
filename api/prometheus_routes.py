from __future__ import annotations

from fastapi import APIRouter, Response

from api.event_log import EventLog
from api.prod_config import config_status
from api.queue_control import QueueControl
from api.redis_queue import RedisQueue
from api.runtime_store import RuntimeStore
from api.storage import SchedulerStore


router = APIRouter()
store = SchedulerStore()
runtime = RuntimeStore()
queue = QueueControl()
log = EventLog()
redis_queue = RedisQueue()


def line(name: str, value: int | float, labels: dict[str, str] | None = None) -> str:
    if labels:
        inner = ",".join(f'{k}="{v}"' for k, v in labels.items())
        return f"{name}{{{inner}}} {value}"
    return f"{name} {value}"


@router.get("/metrics")
def prometheus_metrics() -> Response:
    status = store.status()
    rt = runtime.status()
    qs = queue.snapshot()
    cfg = config_status()
    redis_health = redis_queue.health()
    rows = [
        "# HELP ailovanta_jobs_total Jobs by status",
        "# TYPE ailovanta_jobs_total gauge",
        line("ailovanta_jobs_total", status.get("queued_jobs", 0), {"status": "queued"}),
        line("ailovanta_jobs_total", status.get("assigned_jobs", 0), {"status": "assigned"}),
        line("ailovanta_jobs_total", status.get("done_jobs", 0), {"status": "done"}),
        line("ailovanta_jobs_total", status.get("failed_jobs", 0), {"status": "failed"}),
        "# HELP ailovanta_nodes_total Nodes by state",
        "# TYPE ailovanta_nodes_total gauge",
        line("ailovanta_nodes_total", status.get("nodes", 0)),
        line("ailovanta_verifications_total", status.get("verifications", 0)),
        line("ailovanta_verifications_passed_total", status.get("passed_verifications", 0)),
        line("ailovanta_runtime_models_total", rt.get("models", 0)),
        line("ailovanta_runtime_nodes_total", rt.get("runtimes", 0)),
        line("ailovanta_queue_throttled", 1 if qs.get("throttled") else 0),
        line("ailovanta_queue_queued", qs.get("queued", 0)),
        line("ailovanta_queue_assigned", qs.get("assigned", 0)),
        line("ailovanta_redis_up", 1 if redis_health.get("ok") else 0),
        line("ailovanta_config_postgres", 1 if cfg.get("database_backend") == "postgres" else 0),
    ]
    for level, count in log.summary().get("levels", {}).items():
        rows.append(line("ailovanta_events_total", count, {"level": str(level)}))
    return Response("\n".join(rows) + "\n", media_type="text/plain; version=0.0.4")
