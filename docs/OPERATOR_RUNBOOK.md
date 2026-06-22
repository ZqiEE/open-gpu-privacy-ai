# Operator Runbook

This runbook is for local operators testing the MVP.

## Start API

```bash
make api
```

## Start node

```bash
make node
```

## Seed demo nodes

```bash
python scripts/seed_demo_nodes.py --api-url http://127.0.0.1:8000
```

## Check dashboard

Open:

```text
dashboard.html
reputation.html
```

## Export reputation

```bash
python scripts/export_reputation.py --api-url http://127.0.0.1:8000
```

## Queue maintenance

```bash
make maintain
```

## Health checks

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```
