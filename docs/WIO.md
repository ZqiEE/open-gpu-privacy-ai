# Worker IO

This document defines the current remote worker integration path.

## Create task

```text
POST /wio/task
```

Payload:

```json
{
  "plan": {
    "plan_id": "foundation_plan_1",
    "max_steps": 1,
    "estimated_total_tokens": 128
  },
  "node_id": "node-1",
  "input_uri": "s3://bucket/input.jsonl",
  "output_uri": "s3://bucket/output/"
}
```

Response contains a worker task envelope.

## Submit signed result

```text
POST /wio/result
```

Payload:

```json
{
  "payload": {
    "task_id": "task_x",
    "node_id": "node-1",
    "checkpoint_uri": "s3://bucket/output/checkpoint",
    "checkpoint_hash": "sha256:...",
    "token_count": 128,
    "train_loss": 0.2,
    "eval_loss": 0.2,
    "node_proof": {
      "schema_version": "ailovanta.node_proof.v1"
    }
  },
  "require_valid": true
}
```

The result is verified through node proof before being accepted into outbox.

## Local helper modules

```text
api/wc.py
api/wio.py
api/wio_api.py
```

## Production replacements

```text
input_uri/output_uri -> real object storage
node secret -> real worker credential / attestation
checkpoint_uri -> durable model artifact path
checkpoint_hash -> actual artifact digest
```
