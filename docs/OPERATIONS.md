# Operations

v1.1 adds basic operational workflows for local development.

## Health checks

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

## Queue maintenance

```bash
python scripts/queue_maintenance.py --api-url http://127.0.0.1:8000
```

This runs:

- retry failed jobs
- requeue stale assigned jobs
- print current scheduler status

## Training demo

```bash
python scripts/demo_training_flow.py --api-url http://127.0.0.1:8000
```

This creates a training job and registers a model version.

## Smoke test

```bash
python scripts/smoke_api.py --api-url http://127.0.0.1:8000
```

## Local data

Runtime data is stored under:

```text
runtime_data/
```

It is ignored by Git.
