# Deploy

## Production compose

```bash
cp .env.production.example .env.production
# edit .env.production with real values

docker compose -f docker-compose.prod.yml up -d --build
```

The compose file starts:

```text
api.main_learning
runtime_data persistent volume
HTTP healthcheck
restart policy
```

## HTTPS

Use a real reverse proxy in front of the API:

```text
Cloudflare / Caddy / Nginx / managed load balancer
```

Required:

```text
TLS certificate
AILOVANTA_PUBLIC_BASE_URL=https://your-domain.example
firewall allows only 80/443 externally
admin-only access to runtime_data volume
```

## Readiness

```bash
python scripts/prod_ready.py --result runtime_data/local_loop/foundation_result.json
```

## Release gate

The repository has CI workflow:

```text
.github/workflows/rg.yml
```

It imports and runs release gate logic.

## Backup

At minimum, backup the persistent volume containing:

```text
runtime_data/*.sqlite3
runtime_data/local_loop
runtime_data/artifacts
runtime_data/anchors
runtime_data/parcels
runtime_data/model_monitor
```

Example host command:

```bash
mkdir -p backups
BACKUP_NAME="ailovanta_runtime_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
docker run --rm \
  -v ailovanta_ailovanta_runtime:/data:ro \
  -v "$PWD/backups:/backup" \
  alpine tar -czf "/backup/$BACKUP_NAME" -C /data .
```

Restore example:

```bash
docker compose -f docker-compose.prod.yml down
docker run --rm \
  -v ailovanta_ailovanta_runtime:/data \
  -v "$PWD/backups:/backup" \
  alpine sh -c "rm -rf /data/* && tar -xzf /backup/$BACKUP_NAME -C /data"
docker compose -f docker-compose.prod.yml up -d
```

## Worker path

```text
POST /wio/task
POST /wio/result
```

See `docs/WIO.md`.

## Go-live blockers

Do not go public until these are real:

```text
real GPU worker pool
real model artifacts
external artifact storage or durable model registry
external anchor / chain adapter
monitoring alerts
backup restore drill
rate and abuse controls
security review
```
