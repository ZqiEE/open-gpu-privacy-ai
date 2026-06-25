# Learning Pack to Foundation Pipeline

## Purpose

This bridge turns the latest AutoTruth training pack into a foundation job, then runs the existing foundation pipeline.

## App entrypoint

```bash
uvicorn api.main_learning:app --reload
```

## API

```text
POST /learning/foundation/jobs
POST /learning/foundation/run
```

## One command

```bash
python scripts/run_learning_foundation.py --core-path ../ailovanta-core
```

## Flow

```text
latest learning pack
-> jsonl dataset shard
-> foundation job
-> foundation pipeline
-> foundation artifact
-> public import
-> chain event
-> runtime manifest
```

## Full cycle

```bash
python scripts/run_learning_cycle.py --core-path ../ailovanta-core
python scripts/run_learning_foundation.py --core-path ../ailovanta-core
```

## Meaning

AutoTruth no longer stops at scoring. Its latest training pack can become a foundation training job and enter the model artifact pipeline automatically.
