# Next Milestone

This document defines where feature-building should stop and where real testnet validation begins.

## Current stage

Ailovanta has reached distributed testnet scaffold stage.

Implemented:

```text
public node client
node identity
basic device detection
node testnet bootstrap
job worker registration
runtime pool registration
runtime router
runtime store
node admission rules
worker IO task/result envelopes
node proof / trust registry
artifact chunk manifest
route book
route health
rollback
release gate
prod ready checker
commercial checklist
```

## Stop line for v0

Do not keep adding broad features before this passes:

```text
1. Start gateway API.
2. Register at least one separate node machine.
3. Node appears in /nodes.
4. Node appears in /runtime/nodes.
5. /node-admission/check admits or rejects correctly.
6. Register one model manifest.
7. /runtime/route assigns a capable node.
8. Submit one worker result.
9. Proof / verification path records the result.
10. Build one artifact chunk manifest.
```

When all ten pass, v0 testnet scaffold is complete.

## Next code work only after real run

Only build more after a real test run exposes a gap.

Allowed next work:

```text
validator mesh
storage replica tracking
reward / reputation update loop
signed task envelopes
node dashboard
```

Not allowed before test run:

```text
more branding changes
more deployment documents
more generic commercial checklists
more unrelated API surfaces
claiming production distributed training
```

## Honest status

```text
Code scaffold: yes.
Real distributed network: not yet.
Commercial network: not yet.
Next move: run Node Testnet v0 on real machines.
```
