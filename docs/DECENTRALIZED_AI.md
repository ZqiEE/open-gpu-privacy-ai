# Decentralized AI Ledger

v2.1 adds a local ledger simulation for the AI network.

Files:

```text
api/content_addressing.py
api/decentralized_identity.py
api/contribution_ledger.py
api/task_proof.py
api/network_validator.py
api/model_commit_registry.py
scripts/seed_decentralized_network_demo.py
scripts/decentralized_ledger_report.py
```

Commands:

```bash
python scripts/seed_decentralized_network_demo.py
python scripts/decentralized_ledger_report.py
```

The ledger stores hashes, scores, credits, and model commit records. Large objects stay outside the ledger.
