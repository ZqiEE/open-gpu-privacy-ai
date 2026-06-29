# Dashboard

v1.2 adds a local dashboard for the private AI compute network MVP.

## Static page

Open:

```text
dashboard.html
```

The dashboard reads the local API at:

```text
http://127.0.0.1:8000
```

## API endpoints

```text
GET /dashboard/summary
GET /dashboard/jobs
GET /dashboard/models
GET /dashboard/owned-runtime
```

## What it shows

- node count
- total jobs
- queued jobs
- assigned jobs
- completed jobs
- failed jobs
- verification pass rate
- model version count
- recent jobs
- model versions
- owned runtime route status
- worker validation receipt pass rate
- latest worker validation blockers
- worker validation reputation events

## Owned runtime audit view

`GET /dashboard/owned-runtime` returns the audit chain for owned-model serving:

```text
runtime models and online runtimes
recent runtime route assignments
latest worker validation receipts
worker validation pass rate
reputation events attached to validated worker results
blockers that prevent owned runtime readiness
```

This endpoint is intended for local testnet and ops visibility. It makes the route -> worker -> validation -> reputation chain inspectable without manually querying each subsystem.

## Run flow

```bash
make api
make node
make demo-training
```

Then open `dashboard.html` and click refresh.
