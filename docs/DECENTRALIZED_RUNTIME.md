# Decentralized Runtime Direction

Ailovanta should not treat a central server as the final owner of models, worker output, or proof history.

The current HTTP API and Docker deployment are coordination scaffolding only:

```text
API server        -> task coordination, routing, temporary cache, admin UI
Worker node       -> local compute and signed result submission
Artifact store    -> durable model/checkpoint storage outside the API process
Anchor adapter    -> append-only proof anchor, later chain/external notarization
Runtime node      -> loads artifacts by URI and serves model execution
```

## What must not be centralized long term

```text
model checkpoints
adapter artifacts
worker proof history
promotion receipts
trust anchors
route decisions that need auditability
```

## Current local scaffold

The repository already has local placeholders:

```text
api/artifact_store.py      local artifact file store / external artifact adapter interface
api/anchor_adapter.py      local append-only file anchor / external chain anchor interface
api/wio.py                 worker task/result envelope helpers
api/wio_api.py             worker task/result API
```

Local mode is for development only:

```text
runtime_data/artifacts
runtime_data/anchors/anchor_log.jsonl
runtime_data/*.sqlite3
```

## Production direction

Replace local adapters with external/durable systems:

```text
Artifact storage:
  - S3-compatible object storage
  - Cloudflare R2
  - MinIO
  - IPFS/Filecoin-style content-addressed storage later

Anchor / proof layer:
  - external notarization
  - real chain anchor
  - content hash receipt
  - promotion decision hash

Coordination layer:
  - API server may exist, but it should be replaceable
  - Redis/Postgres are coordination/cache/index layers, not the source of truth for artifact ownership
```

## Correct data path

```text
worker receives task envelope
-> worker writes checkpoint/adapter to durable artifact URI
-> worker submits checkpoint_uri + checkpoint_hash + node_proof
-> verifier checks proof and digest
-> promotion gate emits receipt
-> import builds chunk manifest and replica book entry
-> replica repair planner creates storage repair tasks for weak chunks
-> anchor adapter anchors receipt hash
-> runtime node loads by artifact URI / manifest
```

## Replica repair loop

The distribution gate can block a route when the replica book reports under-replicated chunks. The repair loop turns that blocker into storage work:

```text
replica_book.json
-> scan under-replicated chunks
-> create storage_replica_repair tasks
-> storage node copies chunk to target location
-> task completion adds the copy to replica_book
-> route health distribution gate can pass
```

CLI:

```bash
python scripts/replica_repair.py plan --target-node storage-2
python scripts/replica_repair.py list --status queued
python scripts/replica_repair.py complete <task_id>
```

API:

```text
POST /replicas/repair/plan
GET  /replicas/repair/tasks
POST /replicas/repair/tasks/{task_id}/assign
POST /replicas/repair/tasks/{task_id}/complete
```

Current local repair completion records that a copy exists at a node URI. Production workers must perform the actual artifact transfer before submitting completion.

## Server role

The server is allowed to do:

```text
task scheduling
node registry
runtime routing
temporary cache
admin dashboard
monitoring
indexing artifact metadata
```

The server should not be the only place where final artifacts or proofs exist.

## Why Postgres / Redis still exist

Postgres and Redis are useful for:

```text
fast query index
job queue coordination
monitoring
admin operations
debugging
stress tests
```

They are not the final Web3 trust layer. The long-term source of trust is:

```text
artifact hash
node proof
promotion receipt
external anchor / chain notarization
```
