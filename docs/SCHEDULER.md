# Scheduler Persistence

v0.7 adds a SQLite-backed scheduler store for local development.

The goal is to move beyond in-memory demo state while keeping the project easy to run on one machine. SQLite is the local persistence layer. Later versions can replace it with PostgreSQL and Redis.

## What is persisted

- Nodes
- Node status and heartbeat time
- Jobs
- Job assignment
- Job attempts
- Job completion status
- Results

## Local database path

```text
runtime_data/scheduler.sqlite3
```

This path is ignored by Git.

## Runtime flow

```text
node_client -> POST /nodes/register -> SQLite nodes
node_client -> POST /nodes/heartbeat -> SQLite node status
node_client -> GET  /jobs/next -> SQLite jobs assigned
node_client -> POST /jobs/result -> SQLite results and job status
```

## API status

```bash
curl http://127.0.0.1:8000/network/status
```

Example response:

```json
{
  "nodes": 1,
  "queued_jobs": 2,
  "assigned_jobs": 0,
  "done_jobs": 1,
  "failed_jobs": 0,
  "submitted_results": 1,
  "store": "sqlite",
  "path": "runtime_data/scheduler.sqlite3"
}
```

## Why SQLite first

- Runs locally with no external service
- Good for MVP validation
- Lets the node client keep state across restarts
- Easy to replace with PostgreSQL later

## Next step

v0.8 should add a real queue abstraction:

- PostgreSQL for durable node/job/result data
- Redis for short-lived task queue and locks
- Node reputation rules
- Task retry policy
- Verification workflow
