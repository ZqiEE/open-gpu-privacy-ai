# Parcel Receipts

## Purpose

Worker parcel submissions can now be exported as core-compatible checkpoint receipts.

## Public export

```bash
python scripts/export_parcel_receipts.py \
  --output runtime_data/parcels/checkpoint_receipts.json
```

The export uses schema:

```text
ailovanta.checkpoint_receipt.v1
```

## Public to core aggregation

```bash
python scripts/run_receipt_finalize.py \
  --core-path ../ailovanta-core \
  --plan runtime_data/foundation_plan.json \
  --receipts-output runtime_data/parcels/checkpoint_receipts.json \
  --set-output runtime_data/parcels/checkpoint_set.json
```

## Flow

```text
parcel submitted output
-> public receipt export
-> core aggregate checkpoint receipts
-> checkpoint set
```

This closes the first public-node receipt bridge for distributed checkpoint work.
