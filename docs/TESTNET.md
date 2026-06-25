# Testnet v0

This follows the original Ailovanta design:

```text
public node client
-> gateway registration
-> runtime pool registration
-> task pull / result submit
-> proof / validation
-> artifact chunk manifest
-> route to verified warm runtimes
```

It is not a design where one official server owns all compute and storage.

## Start API

```bash
uvicorn api.main_learning:app --reload
```

## Bootstrap a node

```bash
python -m node_client.testnet \
  --api-url http://127.0.0.1:8000 \
  --region global \
  --engine python \
  --engine local
```

This registers through:

```text
POST /nodes/register
POST /runtime/nodes/register
```

The machine becomes both:

```text
job worker node
runtime pool candidate
```

## Pool selection

```text
no accelerator -> cpu_pool
< 24GB memory -> small_gpu_pool
>= 24GB memory -> large_gpu_pool
```

## Runtime routing

```text
POST /runtime/models/register
POST /runtime/route
```

The router scores machines by:

```text
warm cache
trust score
current load
latency
price
region
privacy tier
```

## Artifact distribution

```bash
python scripts/chunk_manifest.py path/to/model-or-checkpoint.bin \
  --source node://node-1/cache/model.bin \
  --min-replicas 3
```

The manifest records:

```text
artifact_hash
chunk sha256 hashes
chunk sources
replica policy
```

The registry should store this small manifest, not the full model weights.

## Correct early testnet

```text
Machine A: gateway + private core bridge
Machine B: small_gpu_pool worker
Machine C: storage_pool seed/cache node
Machine D: validator_pool node
```

## Avoid

```text
Do not route every request to one official server.
Do not force every node to download every model.
Do not trust artifact sources without hash verification.
Do not send private/protected models to public nodes.
```

## Next implementation steps

```text
node admission rules
validator mesh
reward/reputation updates
storage replica tracking
signed worker task envelopes
public testnet dashboard
```
