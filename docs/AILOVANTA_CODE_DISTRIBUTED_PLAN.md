# Ailovanta-Code Distributed Plan

Ailovanta-Code is the first vertical model direction for Ailovanta.

The next stage is distributed AutoTrain plus distributed model runtime for code tasks.

## Core rule

Every training job is designed as a distributed job from the start.

```text
distributed_required=true
```

Early execution may use local or controlled distributed simulation, but the architecture must be ready for real GPU workers, validator nodes, aggregators, artifact promotion, and Runtime Router execution.

## Target flow

```text
authorized data
-> Rights Proof Registry
-> AutoTrain job
-> distributed worker execution
-> validator checks
-> aggregator merge
-> model artifact
-> promotion gate
-> runtime manifest
-> Runtime Router
-> Ailovanta-Code response
-> feedback into the next training round
```

## Ailovanta-Code scope

Ailovanta-Code focuses on:

- writing code
- fixing code
- explaining errors
- generating tests
- fixing CI
- understanding GitHub repositories
- generating pull request summaries
- producing deployment files

Early target languages and frameworks:

- Python
- JavaScript
- TypeScript
- FastAPI
- React
- Next.js
- Node.js
- SQL
- Docker
- GitHub Actions

## Boundary

This stage must not claim that production global training is complete. It is a local or controlled distributed simulation until real GPU workers, real artifact storage, real attestation, and production runtime pools are connected.
