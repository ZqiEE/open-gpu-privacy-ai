# Worker Safety

v1.7 adds a safer worker execution layer for local MVP nodes.

## Rules

- Only known job types are accepted
- Payload size is limited
- Runtime is capped
- Unknown jobs return a failed result instead of running
- The current runner is still simulated

## Allowed job types

```text
rag_index
rag_import
evaluation
evaluation_batch
verification
lora_micro
```

## Local check

```bash
python scripts/worker_self_check.py
```

## Tests

```bash
python -m pytest tests/test_task_policy.py tests/test_job_runner_policy.py -q
```

## Next hardening steps

- signed job metadata
- isolated worker process
- per-job temp directory
- output size limits
- structured execution logs
