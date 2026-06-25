# Guarded Learning Pipeline

## Purpose

This pipeline prevents raw learning output from updating runtime directly.

It creates a foundation result, runs the core eval gate, and only imports the result into runtime when the gate allows it.

## App entrypoint

```bash
uvicorn api.main_learning:app --reload
```

## API

```text
POST /learning/gate/run
```

## One command

```bash
python scripts/run_guarded_learning.py --core-path ../ailovanta-core
```

## Flow

```text
latest training pack
-> foundation job
-> foundation result
-> eval payload
-> core eval gate
-> promotion decision
-> runtime import only if allowed
```

## Safety rule

```text
reject or rollback -> no runtime import
promote -> import into runtime and chain
shadow -> import only when allow_shadow_import is true
```

## Meaning

Auto learning now has a promotion gate before it can affect the owned runtime.
