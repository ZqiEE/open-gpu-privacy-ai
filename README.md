# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v1.6 Scheduler Intelligence Pack

Includes v1.5 Usage Metering Pack plus capability-aware job routing.

Added in v1.6:

- `api/task_router.py`
- capability-aware `SchedulerStore.next_job()`
- GPU jobs skip CPU-only nodes
- priority-based queued job selection
- memory and CPU matching
- `scripts/seed_routing_demo.py`
- `scripts/route_preview.py`
- `routing.html`
- `docs/SCHEDULER_INTELLIGENCE.md`
- `tests/test_task_router.py`
- `tests/test_scheduler_routing.py`

Existing packs:

- v1.5 Usage Metering Pack
- v1.4 Reputation Pack
- v1.3 Node Identity Pack
- v1.2 Dashboard Pack
- v1.1 Operations Pack
- **v1.0 Engineering Pack**

Main scope:

- Open GPU Network
- Private AI Runtime
- Node Client
- Scheduler Intelligence
- Queue and Verification
- Training Jobs
- Model Version Registry
- Local Dashboard
- Node Reputation
- Usage Metering

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

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
curl http://127.0.0.1:8000/usage/summary
python scripts/export_usage.py --api-url http://127.0.0.1:8000
```

Open:

```text
usage.html
```

## Reputation

```bash
curl http://127.0.0.1:8000/reputation/leaderboard
curl http://127.0.0.1:8000/reputation/summary
python scripts/export_reputation.py --api-url http://127.0.0.1:8000
```

## Node Identity

```bash
python scripts/show_node_identity.py
python node_client/client.py --api-url http://127.0.0.1:8000 --identity-path runtime_data/node_identity.json
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
