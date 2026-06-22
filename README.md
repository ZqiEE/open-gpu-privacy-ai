# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v1.2 Dashboard Pack

Includes the previous v1.1 Operations Pack plus a local dashboard.

Main scope:

- Open GPU Network
- Private AI Runtime
- Node Client
- Scheduler
- Queue and Verification
- Training Jobs
- Model Version Registry
- Local Dashboard

Added in v1.2:

- `api/dashboard.py`
- `GET /dashboard/summary`
- `GET /dashboard/jobs`
- `GET /dashboard/models`
- `dashboard.html`
- `tests/test_dashboard.py`
- `docs/DASHBOARD.md`

Existing operations assets:

- `GET /health`
- `GET /ready`
- `scripts/queue_maintenance.py`
- `scripts/demo_training_flow.py`
- `docs/OPERATIONS.md`
- `docs/DEVELOPER_HANDOFF.md`

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

## Dashboard

Open:

```text
dashboard.html
```

The dashboard reads:

```text
http://127.0.0.1:8000/dashboard/summary
```

## Makefile

```bash
make install
make validate
make test
make api
make node
make smoke
make maintain
make demo-training
```

## Docker

```bash
docker compose up --build
```

## Enable Real Local AI

```bash
ollama pull qwen2.5:3b
uvicorn api.main:app --reload
```

The `/ai/chat` endpoint returns `provider: ollama` when Ollama is running, and `provider: fallback` when it is not.
