# Ailovanta API Reference

Base URL for local runtime:

```text
http://127.0.0.1:8000
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
```

Public app and local dashboard:

```text
GET /app
GET /dashboard
```

## Health and status

```text
GET /
GET /health
GET /ready
GET /network/status
GET /verification/status
GET /dashboard/summary
GET /runtime/status
```

Example:

```bash
curl http://127.0.0.1:8000/network/status
```

## Nodes

```text
POST /nodes/register
POST /nodes/heartbeat
GET  /nodes
```

Register a node:

```bash
curl -X POST http://127.0.0.1:8000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "local-node",
    "cpu_threads": 4,
    "memory_gb": 8,
    "has_gpu": false,
    "gpu_name": null,
    "contribution_percent": 30
  }'
```

Send heartbeat:

```bash
curl -X POST http://127.0.0.1:8000/nodes/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"node_id":"node_xxx","status":"online"}'
```

## Runtime router

```text
POST /runtime/models/register
GET  /runtime/models
POST /runtime/nodes/register
GET  /runtime/nodes
GET  /runtime/status
GET  /runtime/assignments
POST /runtime/route
```

Runtime models, runtime nodes, and route assignments are persisted in SQLite at `runtime_data/runtime.sqlite3` by default.

Register a model manifest:

```bash
curl -X POST http://127.0.0.1:8000/runtime/models/register \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "ailovanta-7b",
    "version": "1.0.0",
    "manifest_hash": "sha256:model7b",
    "privacy_level": "public",
    "min_gpu_memory_gb": 8,
    "allowed_pools": ["small_gpu_pool", "large_gpu_pool", "enterprise_pool"],
    "quantization": "int4",
    "context_length": 8192
  }'
```

Register a warm runtime node:

```bash
curl -X POST http://127.0.0.1:8000/runtime/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "runtime_id": "rt-warm-1",
    "node_id": "node-gpu-1",
    "pool": "small_gpu_pool",
    "region": "us-east",
    "gpu_memory_gb": 24,
    "available_gpu_memory_gb": 16,
    "trust_score": 0.9,
    "current_load": 0.2,
    "price_per_1k_tokens": 0.03,
    "latency_ms": 260,
    "supported_engines": ["vllm"],
    "cached_models": ["ailovanta-7b:1.0.0"]
  }'
```

Route a request:

```bash
curl -X POST http://127.0.0.1:8000/runtime/route \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-1",
    "model_id": "ailovanta-7b",
    "version": "1.0.0",
    "task_type": "chat_completion",
    "privacy_level": "public",
    "latency_target_ms": 1000,
    "max_price_per_1k_tokens": 0.05,
    "region_hint": "us-east",
    "verification_required": true
  }'
```

Read route history:

```bash
curl http://127.0.0.1:8000/runtime/assignments
```

The router prefers warm cached models, correct privacy tier, enough GPU memory, high trust score, low load, low latency, and acceptable price.

## Jobs

```text
GET  /jobs
GET  /jobs/next
POST /jobs/result
POST /jobs/retry-failed
POST /jobs/requeue-stale
```

Fetch a job:

```bash
curl "http://127.0.0.1:8000/jobs/next?node_id=node_xxx"
```

Submit a result:

```bash
curl -X POST http://127.0.0.1:8000/jobs/result \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node_xxx",
    "job_id": "job-rag-001",
    "status": "ok",
    "output_summary": "simulated local result"
  }'
```

## Local AI and memory

```text
POST /ai/chat
GET  /memory
POST /memory
DELETE /memory
GET  /usage/summary
```

Chat request:

```bash
curl -X POST http://127.0.0.1:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain Ailovanta in one sentence.",
    "mode": "open",
    "user_id": "local",
    "remember": false
  }'
```

If Ollama is not running, the API returns a safe local fallback response instead of crashing.

## Training

```text
POST /training/jobs
GET  /training/jobs
POST /models/versions
GET  /models/versions
```

Create a training job:

```bash
curl -X POST http://127.0.0.1:8000/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "rag_import",
    "name": "demo-rag",
    "dataset_uri": "file://demo/docs",
    "base_model": "qwen2.5:3b",
    "max_steps": 100,
    "notes": "local demo"
  }'
```

Register a model version:

```bash
curl -X POST http://127.0.0.1:8000/models/versions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo-model",
    "base_model": "qwen2.5:3b",
    "source_job_id": "train_xxx",
    "notes": "local demo model version"
  }'
```

## Minimal flow

1. Register runtime model
2. Register runtime node with cached model
3. Route runtime request
4. Read runtime assignments
5. Register regular node
6. Fetch next job
7. Submit result
8. Check verification status
9. Create training job
10. Register model version
11. Read dashboard summary

## Smoke test

Start the API first:

```bash
uvicorn api.main:app --reload
```

Then run:

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```
