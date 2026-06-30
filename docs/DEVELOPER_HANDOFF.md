# Ailovanta Developer Handoff

## Current state

Ailovanta is a local MVP for a distributed AI compute network.

Implemented:

- Public product page
- FastAPI runtime
- SQLite scheduler store
- Node client
- Ollama adapter with fallback
- Local memory store
- Queue recovery
- Verification records
- Training job API
- Signed worker task envelopes
- Signed worker result proof checks
- Model version registry
- Docker / Compose
- Tests / CI
- Public/private repository boundary

## Repositories

Public repository:

```text
https://github.com/ZqiEE/ailovanta.git
```

Core repository:

```text
https://github.com/ZqiEE/ailovanta-core.git
```

## Good next tasks

1. Keep the public shell clean and brand-consistent.
2. Keep core network logic in Ailovanta Core.
3. Replace SQLite with PostgreSQL behind the same `SchedulerStore` interface.
4. Add Redis-style queue locking.
5. Add a production dashboard for scheduler status and node health.
6. Add storage replica tracking.
7. Add reward / reputation updates from verified worker results.
8. Add real RAG importer.
9. Add LoRA/QLoRA worker integration.
10. Add OpenAPI examples to each endpoint.

## Avoid for now

- Do not add unrelated vertical apps.
- Do not expand into hardware devices yet.
- Do not claim distributed training is solved.
- Do not put core network logic in the public repository.
- Do not run arbitrary untrusted code on contributor machines.
