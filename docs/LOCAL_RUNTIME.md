# Local Runtime

v0.4 adds a minimal local runtime skeleton. It is not a production network yet. It gives developers a concrete path from static MVP to a working local system.

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

## API Endpoints

```text
GET  /
POST /nodes/register
POST /nodes/heartbeat
GET  /jobs/next
POST /jobs/result
POST /ai/chat
GET  /network/status
```

## Next Engineering Steps

- Add persistent PostgreSQL storage
- Add Redis task queue
- Add real Ollama adapter
- Add local memory storage
- Add GPU detection
- Add task sandboxing
- Add node reputation and verification
