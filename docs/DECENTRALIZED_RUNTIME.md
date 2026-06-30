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

## Model artifact anti-theft rule

Large model artifacts must not be distributed as a naked model directory.

Directory-shaped model outputs, such as Transformers or LoRA folders, are sealed before distribution:

```text
model directory
-> tar package in temporary workspace
-> AES-256-GCM encrypted chunks
-> secure artifact manifest
-> replica_book entry over encrypted chunk hashes
-> encrypted chunk replicas under storage nodes
```

The secure manifest records encrypted artifact hash, plaintext artifact hash, encrypted chunk hashes, plaintext chunk hashes, nonce per chunk, `key_id`, and `anti_theft.key_in_manifest=false`.

The manifest must not contain key material. Storage nodes receive encrypted chunks only. Runtime nodes can reconstruct the model only after an authorized key-release step gives them the artifact key. This keeps distributed storage useful for availability without turning every storage replica into a raw model leak.

Local implementation:

```text
api/secure_artifact_pack.py
runtime_data/secure_artifacts/<storage-node>/<artifact-id>/chunk_000000.enc
runtime_data/artifact_manifests/<artifact-id>.secure.manifest.json
runtime_data/replica_book.json
```

Set the local sealing key with:

```text
AILOVANTA_ARTIFACT_ENCRYPTION_KEY=<base64 AES key>
```

Generate a development key through `api.secure_artifact_pack.generate_artifact_key()`. Production must replace this with node/tenant-bound key release, not a shared plaintext environment variable.

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
python scripts/run_replica_maintenance.py --loop
```

API:

```text
POST /replicas/repair/plan
GET  /replicas/repair/tasks
POST /replicas/repair/tasks/{task_id}/assign
POST /replicas/repair/tasks/{task_id}/complete
```

Current local maintenance performs a real local chunk copy when the source artifact is available as `file://...`: it slices the source artifact chunk, verifies the chunk sha256, writes it under `runtime_data/storage_replicas/`, and then completes the repair task. Production storage workers must perform the equivalent real transfer to their own storage before submitting completion.

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
