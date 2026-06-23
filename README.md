# Ailovanta

> AI powered by the world's distributed compute.

Ailovanta is a distributed AI compute network MVP. The public repository contains the product shell, local API, node client, demo pages, tests, and safe interface examples. The production core stays in a separate private repository.

## What it is

Ailovanta explores a simple loop:

```text
people run useful machines
-> the network gets compute
-> compute runs AI jobs
-> results are verified
-> useful contributors earn access and reputation
```

The current repository is not claiming a finished global training network. It is a working local foundation for the public layer: node registration, heartbeat, job dispatch, result submission, verification, training job records, model version records, dashboard data, and local AI fallback.

## Repositories

Public repository:

```bash
git clone https://github.com/ZqiEE/ailovanta.git
```

Private core repository:

```text
https://github.com/ZqiEE/ailovanta-core.git
```

## Current MVP features

- Public landing page: `index.html`
- Local dashboard: `dashboard.html`
- FastAPI runtime: `api/main.py`
- SQLite scheduler store
- Node registration and heartbeat
- Job queue and result submission
- Lightweight result verification
- Trust updates after verified results
- Queue recovery endpoints
- Training job planner
- Model version registry
- Ollama adapter with graceful fallback
- Local memory list/add/wipe endpoints
- Hardened local node client
- Docker / Compose files
- Validation script and pytest suite

## Quickstart

```bash
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python validate.py
python -m pytest -q
uvicorn api.main:app --reload
```

On Windows PowerShell:

```powershell
git clone https://github.com/ZqiEE/ailovanta.git
cd ailovanta
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python validate.py
python -m pytest -q
uvicorn api.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Run a local node in another terminal:

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

Run the smoke flow after the API is running:

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```

## Core local flow

```text
POST /nodes/register
POST /nodes/heartbeat
GET  /jobs/next
POST /jobs/result
GET  /verification/status
GET  /network/status
POST /training/jobs
POST /models/versions
GET  /dashboard/summary
```

## Public / private boundary

Public repository = product shell, public client, local MVP, demos, docs, tests, and safe interfaces.

Private core repository = core routing, validation, scoring, orchestration, and operator logic.

H-SwarmTrain remains the core algorithm family name.

## Project discipline

Ailovanta should not pretend the hardest part is solved. The current realistic path is:

1. Make the public shell clean and runnable.
2. Keep sensitive core logic outside the public repository.
3. Start with short, verifiable jobs.
4. Add stronger scheduling, verification, and worker isolation.
5. Connect the public shell to Ailovanta Core.
6. Move from local MVP to controlled testnet.

## Docs

- `BRAND.md` — brand rules
- `SECURITY_BOUNDARY.md` — public/private boundary
- `PRIVATE_CORE.md` — private core plan
- `docs/LOCAL_RUNTIME.md` — local run guide
- `docs/API.md` — local API reference
- `docs/ARCHITECTURE.md` — system overview
- `docs/ROADMAP.md` — roadmap
- `docs/DEVELOPER_HANDOFF.md` — developer handoff

## Local check

```bash
python validate.py
python -m pytest -q
```
