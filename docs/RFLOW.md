# RFlow

RFlow connects submitted parcel outputs to the runtime-ready model path.

## API

```text
POST /rflow/run
```

Payload:

```json
{
  "plan_path": "runtime_data/foundation_plan.json",
  "core_path": "../ailovanta-core",
  "result_output": "runtime_data/parcels/foundation_result.json",
  "apply_public": true
}
```

## Flow

```text
submitted parcel outbox
-> checkpoint receipts export
-> core checkpoint set
-> core foundation result
-> public import
-> artifact binding
-> runtime preparation
-> doctor report
```

This turns distributed parcel submissions into a runtime-ready candidate path.
