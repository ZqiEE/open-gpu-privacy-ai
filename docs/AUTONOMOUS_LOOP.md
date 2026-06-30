# Autonomous Loop

## Purpose

Autonomous Loop is the one-shot controller for the Ailovanta automatic learning cycle.

It connects event export, core AutoTruth scoring, public training pack import, guarded learning, optional local checkpoint execution, backend environment passthrough, shadow/live registration, and runtime import rules.

## App entrypoint

```bash
uvicorn api.main_learning:app --reload
```

## API

```text
POST /autonomous/run
GET /autonomous/latest
GET /autonomous/runs
```

## One command

Default guarded cycle:

```bash
python scripts/run_autonomous_loop.py --core-path ../ailovanta-core
```

Run with local checkpoint execution:

```bash
python scripts/run_autonomous_loop.py \
  --core-path ../ailovanta-core \
  --execute-checkpoints \
  --checkpoint-output-root runtime_data/autonomous_checkpoints
```

Run with Transformers backend passthrough:

```bash
python scripts/run_autonomous_loop.py \
  --core-path ../ailovanta-core \
  --execute-checkpoints \
  --model-backend transformers-causal-lm \
  --base-model gpt2 \
  --backend-output-dir runtime_data/autonomous_model \
  --backend-device cpu \
  --backend-max-steps 3
```

## Flow

```text
public learning events
-> export events
-> core AutoTruth
-> import training pack
-> guarded learning pipeline
-> optional core local checkpoint execution
-> optional backend env passthrough
-> eval gate
-> shadow/live monitor
-> runtime import only if allowed
-> run log
```

## Real execution path

When `execute_checkpoints=true`, public sends execution flags to core:

```text
/autonomous/run
-> /learning/gate/run
-> core scripts/run_foundation_job.py --execute-checkpoints
-> local checkpoint executor
-> node adapter
-> model execution backend
-> checkpoint receipt
-> foundation artifact
```

Backend passthrough sets these core environment variables:

```text
AILOVANTA_MODEL_BACKEND
AILOVANTA_BASE_MODEL
AILOVANTA_BACKEND_OUTPUT_DIR
AILOVANTA_BACKEND_DEVICE
AILOVANTA_BACKEND_MAX_STEPS
AILOVANTA_BACKEND_LR
```

## Protection chain

```text
poison check
verifier audit
lineage
score gate
foundation artifact
promotion gate
shadow monitor
rollback executor
```

## Meaning

This is the first complete one-command automatic evolution controller. It does not make the model magically perfect, but it makes the learning cycle auditable, gated, recoverable, and able to execute local checkpoint work with backend configuration when enabled.

## Autonomous Code Loop

The AutoTruth loop works from public learning events. Ailovanta-Code also has a source-driven autonomous loop that does not require user uploads:

```bash
python scripts/run_autonomous_code_training_loop.py \
  --sources runtime_data/github_code_sources.json \
  --core-path ../ailovanta-core
```

API:

```text
POST /autonomous/code/run
GET  /autonomous/code/latest
GET  /autonomous/code/runs
```

This controller discovers/fetches authorized code sources, extracts instruction-first data, builds executable code tasks, runs sandboxed verification, exports verified samples, and only then calls the core foundation pipeline.
