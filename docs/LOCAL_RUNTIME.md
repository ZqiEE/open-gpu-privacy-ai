# Ailovanta Local Runtime

Ailovanta is still a local MVP. It gives developers a concrete path from static demo to a working local system for distributed AI compute.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start API

```bash
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Public app:

```text
http://127.0.0.1:8000/app
```

Local dashboard:

```text
http://127.0.0.1:8000/dashboard
```

## Start Node Client

In another terminal:

```bash
python node_client/client.py --api-url http://127.0.0.1:8000 --contribution 30
```

The node client will:

1. Detect local CPU and memory
2. Register itself with the API
3. Send heartbeat events
4. Pull a small job
5. Simulate execution
6. Submit the result
7. Receive verification and trust updates

## API Endpoints

```text
GET  /
GET  /app
GET  /dashboard
GET  /health
GET  /ready
GET  /network/status
GET  /verification/status
POST /nodes/register
POST /nodes/heartbeat
GET  /jobs
GET  /jobs/next
POST /jobs/result
POST /jobs/retry-failed
POST /jobs/requeue-stale
POST /ai/chat
GET  /dashboard/summary
GET  /dashboard/jobs
GET  /dashboard/models
```

## Next Engineering Steps

- Add persistent PostgreSQL storage
- Add Redis task queue
- Add real worker adapters
- Add GPU worker integration
- Add task sandboxing
- Add node reputation and stronger verification
- Connect public shell to Ailovanta Core
