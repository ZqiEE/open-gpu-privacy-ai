# Ailovanta

[![Ailovanta CI](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml/badge.svg)](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml)

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

The current repository is not claiming a finished global training network. It is a working local foundation for the public layer: node registration, heartbeat, job dispatch, result submission, verification, training job records, model version records, runtime routing, dashboard data, and local AI fallback.

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
- Served app route: `/app`
- Served dashboard route: `/dashboard`
- SQLite scheduler store
- Node registration and heartbeat
- Job queue and result submission
- Lightweight result verification
- Runtime model manifest registry
- Runtime node registry
- Persistent runtime store
- Runtime assignment history
- Warm-cache, trust, privacy, latency, price, and GPU-memory-aware Runtime Router
- Trust updates after verified results
- Queue recovery endpoints
- Training job planner
- Model version registry
- Ollama adapter with graceful fallback
- Local memory list/add/wipe endpoints
- Hardened local node client
- Docker / Compose files
- Validation script and pytest suite
- Contribution guide and issue templates

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

Open after the API starts:

```text
API docs:  http://127.0.0.1:8000/docs
App:       http://127.0.0.1:8000/app
Dashboard: http://127.0.0.1:8000/dashboard
```

Run a local node in another terminal:

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

Run the smoke flow after the API is running:

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```

Run the runtime demo flow after the API is running:

```bash
python scripts/demo_runtime_flow.py --api-url http://127.0.0.1:8000
```

## Core local flow

```text
POST /runtime/models/register
POST /runtime/nodes/register
POST /runtime/route
GET  /runtime/assignments
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

- `VERSION` — current public MVP version
- `BRAND.md` — brand rules
- `CONTRIBUTING.md` — contribution guide
- `SECURITY_BOUNDARY.md` — public/private boundary
- `PRIVATE_CORE.md` — private core plan
- `docs/CHANGELOG.md` — release history
- `docs/PROJECT_STATUS.md` — current done/not-done boundary
- `docs/PUBLIC_LAUNCH_CHECKLIST.md` — public launch checklist
- `docs/RUNTIME_DEMO.md` — runtime demo guide
- `docs/TECHNICAL_OVERVIEW.md` — technical overview
- `docs/MODEL_RUNTIME_ARCHITECTURE.md` — model storage, runtime, routing, and trust architecture
- `docs/CORE_INTEGRATION_PLAN.md` — public/core integration plan
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
