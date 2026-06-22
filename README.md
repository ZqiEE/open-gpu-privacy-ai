# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v2.2 Chain Adapter Pack

Added:

- `api/chain_adapter.py`
- `api/local_chain_adapter.py`
- `api/testnet_chain_adapter.py`
- `api/object_store_adapter.py`
- `contracts/ContributionLedger.sol`
- `scripts/export_ledger_for_chain.py`
- `scripts/simulate_chain_submit.py`
- `scripts/chain_adapter_demo.py`
- `docs/CHAIN.md`
- `tests/test_chain_adapters.py`
- `make chain-demo`
- `make chain-export`
- `make chain-submit`

## v2.1 Decentralized AI Ledger Pack

Added:

- `api/content_addressing.py`
- `api/decentralized_identity.py`
- `api/contribution_ledger.py`
- `api/task_proof.py`
- `api/network_validator.py`
- `api/model_commit_registry.py`
- `scripts/seed_decentralized_network_demo.py`
- `scripts/decentralized_ledger_report.py`
- `docs/DECENTRALIZED_AI.md`
- `tests/test_decentralized_identity.py`
- `tests/test_contribution_ledger.py`
- `tests/test_task_proof_validator.py`
- `tests/test_model_commit_registry.py`
- `make ledger-demo`
- `make ledger-report`

## Chain Adapter Demo

```bash
make chain-demo
make chain-export
make chain-submit
```

## Ledger Demo

```bash
make ledger-demo
make ledger-report
```

## Data Engine

```bash
make data-demo
make data-report
```

## Run Local Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

## Docker

```bash
docker compose up --build
```
