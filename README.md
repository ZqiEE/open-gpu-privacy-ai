# Open GPU Privacy AI MVP

> Run a node, use private AI for free. No node, use paid mode.  
> 开节点，免费用隐私 AI；不开节点，付费用。

A local MVP for a **user-owned GPU network for private AI**. Users contribute idle GPU/CPU through local nodes, and user growth becomes compute growth.

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

## v2.0 Data Engine Pack

Added:

- `api/source_registry.py`
- `api/corpus_pipeline.py`
- `api/web_document_store.py`
- `api/corpus_search.py`
- `api/training_candidate_store.py`
- `scripts/seed_authorized_corpus_demo.py`
- `scripts/corpus_report.py`
- `tests/test_corpus_pipeline.py`
- `tests/test_corpus_source_store.py`
- `make data-demo`
- `make data-report`

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
