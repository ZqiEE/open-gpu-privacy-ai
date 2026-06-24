# Foundation Jobs

## Purpose

Foundation jobs are the public API layer for Ailovanta-owned large model training.

They do not represent a local model tag. They represent a verifiable training intent:

```text
authorized data shards
-> trusted GPU nodes
-> foundation plan in ailovanta-core
-> foundation artifact
-> artifact hash
-> chain registry
-> runtime manifest
-> owned-chat
```

## Endpoint

```text
POST /foundation/jobs
GET /foundation/jobs
GET /foundation/jobs/{job_id}
```

## Payload

```json
{
  "model": {
    "model_id": "ailovanta-owned",
    "target_version": "candidate",
    "parameter_count_b": 1.0
  },
  "dataset_shards": [
    {
      "shard_id": "shard_1",
      "source_id": "src_1",
      "uri": "file://data/shard_1.jsonl",
      "token_count": 100000,
      "allowed_use": "pretrain"
    }
  ],
  "nodes": [
    {
      "node_id": "gpu_1",
      "gpu_memory_gb": 24,
      "gpu_count": 1,
      "trust_score": 0.9
    }
  ],
  "stage": "pretrain",
  "max_steps": 1000
}
```

## Next step

Export queued foundation jobs to `ailovanta-core` and run:

```bash
python scripts/run_foundation_job.py foundation_job.json --output runtime_data/foundation_result.json
```
