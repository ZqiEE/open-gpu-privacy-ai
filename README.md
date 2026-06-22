# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Free access attracts users, users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v0.9 Update

v0.9 adds training jobs and model version registration.

### What changed

- Added `api/training.py`: training job planner
- Updated `api/storage.py`: model version registry and custom training jobs
- Updated `api/main.py`: training and model version APIs
- Added `POST /training/jobs`
- Added `GET /training/jobs`
- Added `POST /models/versions`
- Added `GET /models/versions`
- Added `docs/TRAINING.md`

## Core Positioning

**The user-owned GPU network for private AI.**

Users contribute local compute. The network gets lower-cost AI inference, fine-tuning, evaluation, and data processing capacity. Contributors unlock free AI usage. Non-contributors can use paid mode.

## Current Structure

```text
index.html                    # English-first product MVP
api/main.py                   # FastAPI API using persistent scheduler store
api/storage.py                # SQLite scheduler persistence and queue recovery
api/training.py               # Training job planner
api/verification.py           # Lightweight verification engine
api/ollama_adapter.py         # Optional Ollama local AI adapter
api/memory_store.py           # Local JSON memory storage
node_client/client.py         # Hardened local node client
node_client/device.py         # Device and GPU detection
node_client/resource_guard.py # CPU/memory resource guard
node_client/job_runner.py     # Simulated sandboxed job runner
docs/TRAINING.md              # Training jobs guide
docs/VERIFICATION.md          # Queue and verification guide
docs/SCHEDULER.md             # Scheduler persistence guide
docs/NODE_CLIENT.md           # Node client guide
docs/OLLAMA.md                # Ollama setup guide
docs/LOCAL_RUNTIME.md         # Local runtime instructions
validate.py                   # Repository validation
requirements.txt              # Python dependencies
```

## Run Local Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

In another terminal:

```bash
python node_client/client.py \
  --api-url http://127.0.0.1:8000 \
  --contribution 30 \
  --max-cpu-percent 70 \
  --min-free-memory-gb 1.5
```

Create a training job:

```bash
curl -X POST http://127.0.0.1:8000/training/jobs \
  -H "Content-Type: application/json" \
  -d '{"kind":"rag_import","name":"demo-rag","dataset_uri":"file://local/docs","base_model":"qwen2.5:3b"}'
```

## Enable Real Local AI

```bash
ollama pull qwen2.5:3b
uvicorn api.main:app --reload
```

The `/ai/chat` endpoint returns `provider: ollama` when Ollama is running, and `provider: fallback` when it is not.

## Product Keywords

**Free, private, open, user-owned, robot-ready AI.**

**免费、隐私、开放、共建、机器人。**
