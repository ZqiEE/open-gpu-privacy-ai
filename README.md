# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v1.9 Report Store Pack

Added:

- `node_client/report_store.py`
- `scripts/list_worker_reports.py`
- `scripts/export_worker_reports.py`
- `docs/REPORTS.md`
- `tests/test_report_store.py`
- `make worker-reports`
- `make export-reports`

## v1.8 Worker Reports Pack

Added:

- `node_client/job_descriptor.py`
- `node_client/execution_report.py`
- `scripts/worker_report_demo.py`
- `docs/JOB_DESCRIPTOR.md`
- `tests/test_job_descriptor.py`
- `tests/test_execution_report.py`
- `make worker-report`

## v1.7 Worker Safety Pack

Added in v1.7:

- `node_client/task_policy.py`
- `scripts/worker_self_check.py`
- `docs/WORKER_SAFETY.md`
- `tests/test_task_policy.py`
- `tests/test_job_runner_policy.py`

Existing packs:

- v1.6 Scheduler Intelligence Pack
- v1.5 Usage Metering Pack
- v1.4 Reputation Pack
- v1.3 Node Identity Pack
- v1.2 Dashboard Pack
- v1.1 Operations Pack
- **v1.0 Engineering Pack**

## Run Local Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

In another terminal:

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

## Worker Reports

```bash
make worker-report
make worker-reports
make export-reports
python -m pytest tests/test_report_store.py -q
```

## Worker Check

```bash
python scripts/worker_self_check.py
python -m pytest tests/test_task_policy.py tests/test_job_runner_policy.py -q
```

## Scheduler Intelligence

```bash
python scripts/seed_routing_demo.py
python scripts/route_preview.py --node-id node_route_gpu
```

Open:

```text
routing.html
```

## Usage Metering

```bash
python scripts/simulate_usage.py --api-url http://127.0.0.1:8000
python scripts/export_usage.py --api-url http://127.0.0.1:8000
```

Open:

```text
usage.html
```

## Dashboard

Open:

```text
dashboard.html
```

## Docker

```bash
docker compose up --build
```
