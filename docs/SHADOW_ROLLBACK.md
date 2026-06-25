# Shadow and Auto Rollback

## Purpose

This layer protects the owned runtime from bad automatic upgrades.

A candidate model can be registered as shadow, promoted to live, monitored with live metrics, and rolled back when metrics drop.

## App entrypoint

```bash
uvicorn api.main_learning:app --reload
```

## API

```text
POST /model-monitor/shadow
POST /model-monitor/promote
POST /model-monitor/metrics
POST /model-monitor/rollback-check
GET /model-monitor/shadow
GET /model-monitor/live
GET /model-monitor/actions
```

## Guarded learning integration

```text
learning pack
-> foundation result
-> eval gate
-> shadow registration
-> promote imports runtime and registers live
-> live metrics
-> rollback check
```

## CLI

```bash
python scripts/check_live_metrics.py ailovanta-owned:candidate \
  --metric quality=0.72 \
  --baseline quality=0.90 \
  --max-drop 0.05
```

## Rule

```text
promote -> live registration
shadow -> shadow only
metric drop -> rollback action
```

## Meaning

Automatic learning cannot safely end at model promotion. It needs live monitoring and rollback actions so a bad candidate cannot silently stay in production.
