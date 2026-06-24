# Owned Runtime Production Path

This document describes the real Ailovanta-owned runtime path. It is not the demo path.

## Required services

1. Ailovanta API
2. Ailovanta worker
3. Local or hosted model runtime loaded with the Ailovanta model artifact
4. Registered runtime model manifest
5. Registered trusted runtime node

## Environment

```bash
cp .env.example .env
```

Important values:

```text
OLLAMA_MODEL=ailovanta-owned:candidate
AILOVANTA_DEFAULT_WORKER_URL=http://127.0.0.1:9001
AILOVANTA_MODEL_BACKEND_URL=http://127.0.0.1:8001
AILOVANTA_MODEL_BACKEND_MODEL=ailovanta-owned:candidate
```

## Start API

```bash
uvicorn api.main_owned:app --reload
```

## Start worker

```bash
uvicorn api.worker:app --port 9001 --reload
```

## Register runtime model and trusted node

Run this after the API is up:

```bash
python scripts/register_owned_runtime.py
```

This registers:

```text
model: ailovanta-owned:candidate
node: node-owned-1
runtime: rt-owned-1
pool: trusted_runtime_pool
```

## Readiness check

```bash
python scripts/check_owned_runtime_ready.py
```

## Owned-chat smoke call

```bash
python scripts/call_owned_chat.py
```

The call must return:

```text
owned_model_ready: true
source: ailovanta-worker-local-runtime or ailovanta-worker-backend
```

## Real production rule

The worker must return a response from a configured model runtime, not fixed text. The runtime manifest hash must come from the promoted core artifact hash or a stable sha256 manifest hash.

## Current status

The repository now supports this path:

```text
core result
-> artifact hash
-> runtime model manifest
-> trusted runtime node
-> owned chat
-> worker inference
```

The remaining external requirement is an actual model runtime process with the Ailovanta artifact loaded.
