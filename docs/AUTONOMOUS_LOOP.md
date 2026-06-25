# Autonomous Loop

## Purpose

Autonomous Loop is the one-shot controller for the Ailovanta automatic learning cycle.

It connects event export, core AutoTruth scoring, public training pack import, guarded learning, shadow/live registration, and runtime import rules.

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

```bash
python scripts/run_autonomous_loop.py --core-path ../ailovanta-core
```

## Flow

```text
public learning events
-> export events
-> core AutoTruth
-> import training pack
-> guarded learning pipeline
-> eval gate
-> shadow/live monitor
-> runtime import only if allowed
-> run log
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

This is the first complete one-command automatic evolution controller. It does not make the model magically perfect, but it makes the learning cycle auditable, gated, and recoverable.
