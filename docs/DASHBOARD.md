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

## Run flow

```bash
make api
make node
make demo-training
```

Then open `dashboard.html` and click refresh.
