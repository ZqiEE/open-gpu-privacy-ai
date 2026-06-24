# Ailovanta

[![Ailovanta CI](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml/badge.svg)](https://github.com/ZqiEE/ailovanta/actions/workflows/validate.yml)

> AI powered by the world's distributed compute.

Ailovanta is a distributed AI compute network MVP. The current public product path is **guest-first chat**: open the app, ask a question, keep conversation history, and continue without login or payment.

## Current MVP rule

```text
No required login.
No required payment.
No required wallet.
Guest mode first.
```

GitHub OAuth and payment docs may exist for later, but they are not the default user path.

## Current model backend truth

The current chat inference path uses a **local bootstrap runtime** through Ollama. It is not Alibaba Cloud, not DashScope, and not yet a production Ailovanta-owned foundation model.

The intended Ailovanta-owned model path is:

```text
public training job
-> ailovanta-core H-SwarmTrain Lite round
-> validation and aggregation
-> artifact metadata
-> model version
-> runtime manifest
-> trusted runtime pool
```

See `docs/MODEL_BACKEND.md` for the exact boundary.

## What it is

Ailovanta explores a simple loop:

```text
people run useful machines
-> the network gets compute
-> compute runs AI jobs
-> results are verified
-> useful contributors earn access and reputation
```

The repository is not claiming a finished global training network. It is a working local foundation for the public layer: guest chat, persistent conversations, native run API, compatibility chat API, node registration, heartbeat, job dispatch, result submission, verification, training job records, model version records, runtime routing, dashboard data, and local AI fallback.

## Main user path

```text
1. Open /app.
2. Browser creates guest_id.
3. User sends a message.
4. Frontend calls POST /ailovanta/v1/chat.
5. Backend creates or reuses conversation_id.
6. Backend saves user and assistant messages.
7. Backend uses recent conversation history for follow-up turns.
8. User can reload, continue, load, or delete conversations.
```

## Main APIs

```text
POST /ailovanta/v1/chat
GET  /ailovanta/v1/conversations
GET  /ailovanta/v1/conversations/{conversation_id}/messages
DELETE /ailovanta/v1/conversations/{conversation_id}

POST /ailovanta/v1/run
POST /v1/chat/completions

GET  /reputation/leaderboard
GET  /reputation/summary

POST /usage/events
GET  /usage/events
GET  /usage/summary
```

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

- Guest-first chat UI in `index.html`
- No login wall and no payment wall
- Browser `guest_id`
- Conversation list, load, new chat, and delete chat
- Native chat endpoint: `/ailovanta/v1/chat`
- Native run endpoint: `/ailovanta/v1/run`
- Persistent conversation store
- Conversation context builder
- Ollama adapter with chat-history support
- Compatibility chat endpoint: `/v1/chat/completions`
- Runtime model manifest registry
- Runtime node registry
- Runtime assignment history
- Warm-cache, trust, privacy, latency, price, and GPU-memory-aware Runtime Router
- Node registration and heartbeat
- Job queue and result submission
- Lightweight result verification
- Reputation endpoints
- Usage event endpoints
- Training job planner
- Model version registry
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

Windows PowerShell:

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
App:       http://127.0.0.1:8000/app
API docs:  http://127.0.0.1:8000/docs
Dashboard: http://127.0.0.1:8000/dashboard
```

## Local check

```bash
python validate.py
python -m pytest -q
```

## Docs

- `docs/MODEL_BACKEND.md` — current bootstrap model boundary and Ailovanta-owned model path
- `docs/NEXT_STAGE_PRD.md` — guest chat core product requirements
- `docs/NEXT_STAGE_CODEX_TASKS.md` — execution plan for guest chat core
- `docs/AUTH_MODEL.md` — guest-first access model
- `docs/PAYMENT_MODEL.md` — payment deferred model
- `docs/NATIVE_RUN_API.md` — native run API guide
- `docs/V1_CHAT_API.md` — compatibility chat API guide
- `docs/RUNTIME_DEMO.md` — runtime demo guide
- `docs/MODEL_RUNTIME_ARCHITECTURE.md` — model storage, runtime, routing, and trust architecture
- `docs/CORE_INTEGRATION_PLAN.md` — public/core integration plan

## Final product principle

```text
First prove value.
Then add identity.
Then add payment.
```
