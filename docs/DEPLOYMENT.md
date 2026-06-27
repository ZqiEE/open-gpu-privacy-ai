# Ailovanta Deployment

Ailovanta can run locally, with Docker Compose, or as Ubuntu systemd services.

## Local API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main_code:app --host 0.0.0.0 --port 8000 --reload
```

Runtime node:

```bash
uvicorn api.runtime_server:app --host 0.0.0.0 --port 9001
```

## Docker Compose

```bash
docker compose up --build
```

API:

```text
http://127.0.0.1:8000
```

Runtime node:

```text
http://127.0.0.1:9001
```

## Production Compose

Postgres, Redis, Prometheus, Grafana, API, and Runtime:

```bash
docker compose -f docker-compose.prod.yml up --build
```

Prometheus:

```text
http://127.0.0.1:9090
```

Grafana:

```text
http://127.0.0.1:3000
```

Prometheus scrape endpoint:

```text
GET /metrics
```

## Ubuntu systemd

```bash
bash scripts/install_ubuntu.sh
```

Edit environment values:

```bash
sudo nano /etc/ailovanta/ailovanta.env
```

Restart:

```bash
sudo systemctl restart ailovanta-api
sudo systemctl restart ailovanta-runtime
```

Logs:

```bash
journalctl -u ailovanta-api -f
journalctl -u ailovanta-runtime -f
```

## Admin panel

Basic panel:

```text
http://127.0.0.1:8000/admin
```

Secure panel with browser-stored admin header:

```text
http://127.0.0.1:8000/admin-secure
```

## Nginx

```bash
sudo cp deploy/nginx/ailovanta.conf /etc/nginx/sites-available/ailovanta.conf
sudo ln -s /etc/nginx/sites-available/ailovanta.conf /etc/nginx/sites-enabled/ailovanta.conf
sudo nginx -t
sudo systemctl reload nginx
```

Replace `api.example.com` and `runtime.example.com` with real domains.

## Node keys

Set admin token:

```bash
export AILOVANTA_ADMIN_TOKEN=change-me-admin
```

Issue:

```bash
curl -X POST http://127.0.0.1:8000/node-keys/issue \
  -H 'Content-Type: application/json' \
  -H 'X-Ailovanta-Admin-Token: change-me-admin' \
  -d '{"node_id":"node-001"}'
```

Rotate:

```bash
curl -X POST http://127.0.0.1:8000/node-keys/node-001/rotate \
  -H 'X-Ailovanta-Admin-Token: change-me-admin'
```

Revoke:

```bash
curl -X POST http://127.0.0.1:8000/node-keys/node-001/revoke \
  -H 'X-Ailovanta-Admin-Token: change-me-admin'
```

## HumanEval

```bash
python scripts/download_humaneval.py --output runtime_data/benchmarks/HumanEval.jsonl
```

Run benchmark endpoint after candidate outputs exist.

## Object storage

```bash
pip install -r requirements-object.txt
```

```bash
export AILOVANTA_S3_ENDPOINT=https://example.r2.cloudflarestorage.com
export AILOVANTA_S3_BUCKET=ailovanta-artifacts
export AILOVANTA_S3_REGION=auto
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
```

## Postgres / Redis

The production compose file sets:

```text
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

Current code keeps SQLite as the safe local default and exposes Postgres/Redis health/config so production migration can be staged without breaking local development.

## Dynamic scheduling

```text
GET  /ops/scheduler/preview
POST /ops/scheduler/reprioritize
```

## Multi-node stress test

```bash
python scripts/stress_nodes.py --server http://127.0.0.1:8000 --nodes 50 --duration 120
```

## Runtime object load

Runtime node can pull an object-store artifact and load it:

```text
POST /load-object
```

## Production notes

Before public deployment, keep these enabled:

- Node keys
- Runtime key
- HTTPS
- Nginx reverse proxy
- Object storage for artifacts
- HumanEval/pytest benchmark gates
- Prometheus/Grafana monitoring
- Queue limits
- Artifact rollback
