# Prod Ready

Run readiness check:

```bash
python scripts/prod_ready.py \
  --result runtime_data/local_loop/foundation_result.json \
  --route-key owned-chat/default
```

It checks:

```text
config
route health
artifact store adapter
anchor adapter
result file
runtime readiness
```

Environment template:

```text
.env.production.example
```

Do not commit real secrets.

## Adapter entries

```text
api/artifact_store.py
api/anchor_adapter.py
api/prod_config.py
api/prod_ready.py
```

Current local adapters:

```text
local artifact file store
file append-only anchor log
```

Production replacements later:

```text
object storage / model registry
real chain or external notarization
real GPU workers
real model checkpoints
remote worker credentials
runtime pool monitoring
backup and recovery
rate limits
security review
```

## Code-ready now

```text
node proof
node trust registry
proof-gated receipts
checkpoint set
artifact v2
promotion gate with proof/trust guardrails
gated apply
active route
route health
rollback route disable/restore
owned-chat default active route
preflight
prod readiness checker
```

## Deployment path

```text
1. Run python scripts/aio.py --core-path ../ailovanta-core
2. Run python scripts/prod_ready.py --result runtime_data/local_loop/foundation_result.json
3. Replace local demo node with real worker.
4. Replace local checkpoint payload with real GPU output.
5. Replace local artifact store with durable model storage.
6. Replace file anchor with external anchor adapter.
7. Remove readiness blockers.
8. Deploy behind HTTPS with monitoring.
```
