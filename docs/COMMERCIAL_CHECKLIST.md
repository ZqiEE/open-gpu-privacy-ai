# Commercial Checklist

This checklist is the gap between the local owned-runtime scaffold and a commercial distributed deployment.

## Code gate

```text
python validate.py
python -m pytest -q
python scripts/aio.py --core-path ../ailovanta-core
python scripts/prod_ready.py --result runtime_data/local_loop/foundation_result.json
```

## Required external resources

```text
HTTPS domain / gateway entry
production database or durable SQLite volume strategy
public node clients installed on independent machines
external machines contributing GPU/CPU/storage capacity
distributed artifact cache / chunk storage / model registry manifest
real model checkpoint files and chunk manifests
worker credentials / attestation / node proof
external anchor / chain adapter or durable notarization
monitoring and alerting
backup and recovery
rate limits and abuse controls
security review
incident rollback process
```

## Must pass before public commercial use

```text
release gate returns release_pass
prod_ready returns production_ready
route_health returns ok
owned-chat-default returns owned_model_ready true
rollback disables/restores active route
worker result requires valid node proof
artifact manifest has chunk hashes and replica sources
anchor record exists for promoted artifact or checkpoint set
runtime router assigns work to verified capable nodes
```

## Current local scaffold

```text
LocalArtifactStore
FileAnchorAdapter
RouteBook
RouteHealth
ReleaseGate
Worker IO API
AIO local loop
node_client testnet bootstrap
runtime pool registration
chunk manifest builder
```

## Do not claim until true

```text
Do not claim production foundation model until real trained weights exist.
Do not claim real decentralization until external anchor, distributed storage, and independent workers exist.
Do not claim commercial reliability until monitoring, backups, security review, and abuse controls exist.
Do not claim Ailovanta owns a GPU cloud; the design is verified external nodes contributing compute.
```