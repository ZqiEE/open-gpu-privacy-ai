# Backup and Recovery

Use the ops-ready app entry when backup APIs are needed:

```bash
uvicorn api.main_ops_ready:app --host 0.0.0.0 --port 8000
```

Configure backup location:

```text
AILOVANTA_BACKUP_PATH=runtime_data/backups
```

Create a snapshot:

```text
POST /ops/backups
```

List snapshots:

```text
GET /ops/backups
```

Verify latest snapshot:

```text
GET /ops/backups/latest
```

Verify one snapshot:

```text
GET /ops/backups/{snapshot_id}/verify
```

Dry-run restore:

```text
POST /ops/backups/{snapshot_id}/restore
{"dry_run": true}
```

Apply restore:

```text
POST /ops/backups/{snapshot_id}/restore
{"dry_run": false}
```

Enhanced readiness includes backup status:

```text
GET /ops/readiness/plus?route_key=owned-chat/default&verify_bytes=true
```

If no valid snapshot exists, enhanced readiness returns a backup blocker.
