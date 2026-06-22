# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

## v2.3 Distributed Model Registry Pack

Added:

- `api/model_package.py`
- `api/distributed_model_registry.py`
- `api/model_node_inventory.py`
- `api/model_router.py`
- `scripts/seed_distributed_model_demo.py`
- `scripts/model_report.py`
- `tests/test_model_package.py`
- `tests/test_distributed_model_registry.py`
- `tests/test_model_node_inventory.py`
- `tests/test_model_router.py`
- `make model-demo`
- `make model-report`

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

## Model Registry Demo

```bash
make model-demo
make model-report
```

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
