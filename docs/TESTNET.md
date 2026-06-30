# Testnet v0

This follows the original Ailovanta design:

```text
public node client
-> local resource guard
-> gateway registration
-> node admission check
-> runtime pool registration
-> task pull / result submit
-> proof / validation
-> model shard delta files
-> delta index / hash check
-> credit ledger
-> checkpoint build
-> checkpoint runtime
-> route to verified warm runtimes
```

It is not a design where one official server owns all compute and storage. Nodes contribute spare compute, storage, and bandwidth without taking over the user's machine.

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

## One-command local loop

Install torch first:

```bash
pip install torch
```

Create a local data file:

```bash
mkdir -p runtime_data
printf "Ailovanta trains model shards on distributed user nodes.\n" > runtime_data/train.txt
```

Run the full local loop:

```bash
python scripts/full_local_loop.py \
  --api-url http://127.0.0.1:8000 \
  --data-file runtime_data/train.txt \
  --total-tokens 120 \
  --shard-tokens 32 \
  --node-runs 4
```

## Local v0 readiness check

Before running separate machines, verify the scaffold still passes the v0 stop line:

```bash
python scripts/testnet_v0_check.py
```

This checks:

```text
gateway API
node registration
/nodes visibility
/runtime/nodes visibility
node admission
model manifest registration
runtime routing
signed worker result submission
signed worker task envelope
proof verification record
artifact chunk manifest
artifact runtime binding
owned chat through artifact-bound worker
worker validation receipt
owned runtime dashboard audit
```

This performs:

```text
create /swarm-model/plans
run node_client.once_real repeatedly
write runtime_data/model_deltas/<plan_id>/*.pt
scan verified delta index into runtime_data/didx.json
award verified node credits into runtime_data/credits.json
build runtime_data/merged_models/*.pt
```

Inspect verified deltas and node credits:

```bash
python scripts/didx.py --scan --award
```

Run the latest merged checkpoint:

```bash
python scripts/rck.py --text "Hello Ailovanta"
```

Or run through HTTP:

```bash
curl -X POST http://127.0.0.1:8000/ck/run \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello Ailovanta","max_new":80}'
```

## Manual real model shard loop

Create shard jobs:

```bash
curl -X POST http://127.0.0.1:8000/swarm-model/plans \
  -H "Content-Type: application/json" \
  -d '{"dataset_uri":"file://runtime_data/train.txt","total_tokens":120,"shard_tokens":32,"min_gpu_memory_gb":0,"enqueue":true}'
```

Run one shard and exit:

```bash
python -m node_client.once_real --api-url http://127.0.0.1:8000 --allow-on-battery
```

Or start the long-running real node client:

```bash
python -m node_client.client_real \
  --api-url http://127.0.0.1:8000 \
  --max-runtime-seconds 120
```

The node writes shard outputs to:

```text
runtime_data/model_deltas/<plan_id>/*.pt
```

Index and verify submitted deltas:

```bash
python scripts/didx.py --scan --plan-id <plan_id> --award
```

Build a merged checkpoint from verified shard outputs:

```bash
python scripts/mck.py \
  --plan-id <plan_id> \
  --model-id ailovanta-foundation \
  --version v0.1
```

Or build through HTTP:

```bash
curl -X POST http://127.0.0.1:8000/ck/build \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"<plan_id>","model_id":"ailovanta-foundation","version":"v0.1"}'
```

## Resource guard

Ailovanta Node should only use spare resources. The local guard checks:

```text
CPU usage
free system memory
GPU utilization
GPU memory usage
GPU temperature
Windows user idle time
battery / plugged-in status
```

Example safe contribution modes:

```bash
# Light: only after 5 minutes idle, conservative GPU use.
python -m node_client.client_real \
  --max-cpu-percent 35 \
  --max-gpu-percent 35 \
  --max-gpu-memory-percent 35 \
  --max-gpu-temperature-c 70 \
  --min-idle-seconds 300

# Balanced: default-like contribution, still pauses on heat/battery/high load.
python -m node_client.client_real \
  --max-cpu-percent 60 \
  --max-gpu-percent 60 \
  --max-gpu-memory-percent 60 \
  --max-gpu-temperature-c 75 \
  --min-idle-seconds 60

# High contribution: user explicitly allows heavier work.
python -m node_client.client_real \
  --max-cpu-percent 80 \
  --max-gpu-percent 80 \
  --max-gpu-memory-percent 80 \
  --max-gpu-temperature-c 78
```

Default behavior pauses on battery power. Use `--allow-on-battery` only when the user explicitly allows it.

## Pool selection

```text
no accelerator -> cpu_pool
< 24GB memory -> small_gpu_pool
>= 24GB memory -> large_gpu_pool
```

## Node admission

Before a node should be trusted as an active runtime, check admission:

```text
GET  /node-admission/rules
POST /node-admission/check
POST /node-admission/choose-pool
```

Admission checks:

```text
pool type
online status
GPU requirement
minimum GPU memory
trust score
current load
heartbeat freshness
trusted/private pool restrictions
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
Do not run heavy GPU work while the user's machine is hot, busy, or on battery.
```

## Next implementation steps

```text
real transformer shard worker
checkpoint pause/resume
validator mesh
reward/reputation updates
storage replica tracking
signed worker task envelopes
public testnet dashboard
```
