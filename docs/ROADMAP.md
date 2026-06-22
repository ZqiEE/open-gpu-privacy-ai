# Roadmap

## v0.1 Public MVP

- Static web demo
- Contributor/free-use model
- Paid/no-node model
- Ephemeral chat
- Open mode
- Private memory demo
- Training engine simulation

## v0.2 Global Demo

- English-first homepage and README
- Compute network dashboard
- Better access gate
- Investor narrative page
- Upgraded training simulator
- Focused private AI positioning

## v0.3 Product Skeleton

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
- Simulated sandboxed job runner
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
