# Queue and Verification

v0.8 adds queue recovery and a first verification layer.

This is still a local MVP skeleton. It does not claim production-grade security. The goal is to stop treating every submitted result as automatically trusted.

## New features

- Result verification engine
- Verification records in SQLite
- Node trust adjustment after verification
- Failed job retry endpoint
- Stale assigned job requeue endpoint
- Verification status endpoint

## Endpoints

```text
POST /jobs/result
POST /jobs/retry-failed
POST /jobs/requeue-stale
GET  /verification/status
GET  /network/status
```

## Submit result flow

```text
node submits result
  -> scheduler stores result
  -> verification engine scores result
  -> verification record is stored
  -> node trust is adjusted
  -> network status updates
```

## Retry failed jobs

```bash
curl -X POST "http://127.0.0.1:8000/jobs/retry-failed?max_attempts=3"
```

## Requeue stale jobs

```bash
curl -X POST "http://127.0.0.1:8000/jobs/requeue-stale?older_than_minutes=30"
```

## Verification status

```bash
curl http://127.0.0.1:8000/verification/status
```

## Production gaps

Before public nodes, the project still needs:

- Signed jobs
- Node authentication
- Redundant execution
- Deterministic test tasks
- Reputation-weighted scoring
- Abuse detection
- Sandboxed workloads
- Encrypted transport
