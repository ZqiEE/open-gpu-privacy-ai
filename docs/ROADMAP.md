# Ailovanta Roadmap

## Current status

Ailovanta is a local MVP. The public repository is meant to be clean, runnable, and understandable. It should not claim that global distributed training is solved yet.

## v0.1 Public MVP

- Static web demo
- Contributor/free-use model
- Paid/no-node model
- Ephemeral chat demo
- Training simulation

## v0.2 Product Shell

- English-first homepage and README
- Compute network dashboard
- Better access gate
- Investor narrative page
- Upgraded training simulator

## v0.3 Public Interface

- Node Client page
- API skeleton page
- Protocol page
- Pricing page
- Waitlist page
- More realistic build path

## v0.4 Local Runtime Skeleton

- FastAPI scheduler/API skeleton
- Local node client simulation
- requirements.txt
- Local runtime guide
- Node register / heartbeat / job dispatch / result submit endpoints

## v0.5 Local AI Runtime

- Ollama adapter
- `/ai/chat` tries local model first
- Graceful fallback when Ollama is unavailable
- Local JSON memory store
- `/memory` list/add/wipe endpoints
- Ollama setup guide

## v0.6 Node Client Hardening

- Device and NVIDIA GPU detection
- CPU and memory resource guard
- Heartbeat stability
- HTTP retry with backoff
- Simulated job runner
- Local node logs

## v0.7 Scheduler Persistence

- SQLite scheduler store for local development
- Persistent nodes, jobs, and results
- Job assignment state
- Job attempts and completion status
- `/network/status` backed by persisted data

## v0.8 Queue and Verification

- Lightweight verification engine
- Verification records in SQLite
- Failed-job retry endpoint
- Stale assigned job requeue endpoint
- Verification status endpoint
- Trust adjustment after result scoring

## v0.9 Training Jobs

- Training job planner
- RAG import job schema
- LoRA micro job schema
- Evaluation batch job schema
- Private memory tuning job schema
- Model version registry

## v1.0 Focused Network MVP

- Stable local runtime
- Stable node client
- Scheduler persistence
- Training job lifecycle
- Model version registry
- Clean documentation and deployment path
- Brand-consistent public repository
- Public/private repository boundary

## v1.1 Controlled Testnet

- Authenticated nodes
- Signed task payloads
- Stronger worker policy
- Better verification records
- PostgreSQL backend option
- Queue locking
- Operator dashboard

## v1.2 Real Worker Layer

- RAG worker
- Evaluation worker
- LoRA/QLoRA worker prototype
- Worker capability registry
- Model artifact metadata registry
- Clear separation between public worker shell and core coordination

## v1.3 Ailovanta Core Integration

- Public shell talks to Ailovanta Core through stable interfaces
- H-SwarmTrain Lite round orchestration connects to public job lifecycle
- Result manifests connect to model version records
- Safer node admission and scoring rules

## Non-goals for now

- Do not claim global distributed training is already solved.
- Do not run arbitrary untrusted code on contributor machines.
- Do not put core network logic in the public repository.
- Do not add unrelated vertical apps before the infrastructure is credible.
