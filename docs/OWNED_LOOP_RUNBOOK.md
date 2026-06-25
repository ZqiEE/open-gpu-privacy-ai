# Owned Loop Runbook

## Goal

This runbook describes the local code-level owned-runtime loop.

It is designed to make the repository ready for real GPU workers, real submitted checkpoints, real artifact promotion, and real runtime routing later.

It does not claim that a production Ailovanta foundation model already exists.

## One command

```bash
python scripts/aio.py --core-path ../ailovanta-core
```

## What it runs

```text
preflight
-> local plan
-> node trust registration
-> signed node result
-> proof-required receipt export
-> core checkpoint set
-> foundation artifact v2
-> promotion gate with proof/trust guardrails
-> gated runtime apply
-> final report
```

## Expected success shape

```json
{
  "ok": true,
  "final": {
    "stage": "runtime_ready",
    "blockers": []
  }
}
```

## Preflight only

```bash
python scripts/preflight.py --core-path ../ailovanta-core
```

## Local loop only

```bash
python scripts/local_loop.py --core-path ../ailovanta-core
```

## Final report only

```bash
python scripts/final_report.py runtime_data/local_loop/foundation_result.json
```

## Main generated files

```text
runtime_data/local_loop/foundation_plan.json
runtime_data/parcels/checkpoint_receipts.json
runtime_data/local_loop/checkpoint_set.json
runtime_data/local_loop/foundation_result.json
runtime_data/local_loop/local_loop_report.json
```

## Production replacements later

```text
local demo node -> real worker node
local proof secret -> real worker credential / attestation system
simulated checkpoint payload -> real GPU training output
local artifact file -> real model weight artifact
local append registry -> real chain anchor
local runtime node -> production runtime pool
```

## Hard gates

The owned loop currently blocks unsafe runtime preparation when:

```text
proof_coverage < 0.8
avg_trust_score < 0.75
runtime doctor reports blockers
artifact hash is missing
```

## Current truth

The code path is ready for local demo validation. Real production use still needs infrastructure: GPUs, remote workers, durable artifact storage, real model loaders, and chain anchoring.
