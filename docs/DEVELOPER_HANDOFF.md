# Developer Handoff

## Current state

The repository is a local MVP for a user-owned GPU network for private AI.

Implemented:

- Static product page
- FastAPI runtime
- SQLite scheduler store
- Node client
- Ollama adapter with fallback
- Local memory store
- Queue recovery
- Verification records
- Training job API
- Model version registry
- Docker / Compose
- Tests / CI

## Good next tasks

1. Replace SQLite with PostgreSQL behind the same `SchedulerStore` interface.
2. Add Redis-style queue locking.
3. Add node identity persistence.
4. Add signed task payloads.
5. Add real RAG importer.
6. Add LoRA/QLoRA worker integration.
7. Add OpenAPI examples to each endpoint.
8. Add a small web dashboard for scheduler status.

## Avoid for now

- Do not add unrelated vertical apps.
- Do not expand into hardware devices yet.
- Do not claim distributed training is solved.
- Do not run arbitrary untrusted code on contributor machines.
