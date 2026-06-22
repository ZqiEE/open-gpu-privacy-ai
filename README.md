# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v1.3 Node Identity Pack

Includes v1.2 Dashboard Pack plus persistent node identity.

Added in v1.3:

- `node_client/identity.py`
- `runtime_data/node_identity.json`
- `scripts/show_node_identity.py`
- `docs/NODE_IDENTITY.md`
- `tests/test_local_identity.py`
- `tests/test_node_registry.py`
- `GET /nodes`
- `GET /dashboard/nodes`
- `POST /nodes/register` can reuse an existing `node_id`

Existing packs:

- v1.2 Dashboard Pack
- v1.1 Operations Pack
- **v1.0 Engineering Pack**

Main scope:

- Open GPU Network
- Private AI Runtime
- Node Client
- Scheduler
- Queue and Verification
- Training Jobs
- Model Version Registry
- Local Dashboard

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
