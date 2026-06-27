# WIO Checkpoint Flow

This is the next step after the trust-flow demo: replace the local demo artifact with a task/result path that matches the Worker IO contract.

## Start API

```bash
export AILOVANTA_CHAIN_ANCHOR=http
export AILOVANTA_CHAIN_ANCHOR_URI=http://127.0.0.1:8000/notary/mock/anchor
export AILOVANTA_NODE_SECRETS_JSON='{"demo-node":"demo-secret"}'
uvicorn api.main_code:app --host 0.0.0.0 --port 8000 --reload
```

## Run checkpoint receipt flow

```bash
python scripts/demo_checkpoint_receipt_flow.py
```

Loose mode for debugging only:

```bash
python scripts/demo_checkpoint_receipt_flow.py --loose
```

## What it does

```text
POST /wio/task
-> claim task
-> create local checkpoint metadata
-> sign checkpoint receipt
-> POST /wio/result
-> POST /catalog/from-receipt
-> validate
-> notarize
-> publish
```

## Submit an existing checkpoint

If a real local GPU job already produced a checkpoint/adapter file:

```bash
python scripts/submit_local_receipt.py \
  --node-id demo-node \
  --node-secret demo-secret \
  --task-id task_x \
  --checkpoint /path/to/checkpoint_or_adapter
```

Then register it into catalog:

```text
POST /catalog/from-receipt
```

## Boundaries

This path does not execute arbitrary remote code. The worker side submits a local artifact that already exists, signs the receipt, and lets the API verify and index it.

Postgres/Redis are still only coordination/index layers. The trust path remains artifact URI, artifact hash, worker receipt, anchor receipt, and runtime manifest.
