# Ailovanta Data Rights Registry

## Purpose

Ailovanta needs a machine-readable registry for data sources before those sources can be used by training jobs.

This lets the system answer three questions:

```text
Who approved this source?
What is the approved scope?
Which model-building uses are allowed?
```

## Source record

Each source record stores:

```text
source_id
source_uri
source_type
authorized_by
authorization_basis
allowed_uses
scope_note
proof_uri
status
```

## Source types

```text
owner_authorized
partner
licensed
uploaded
public_domain
open_dataset
```

## Allowed uses

```text
index
rag
inference
finetune
pretrain
eval
```

## Training link

Training jobs should attach a `data_source_id`. Before the job goes to `ailovanta-core`, the public layer should check whether the data source allows the required use.

```text
rag_import -> rag
lora_micro -> finetune
evaluation_batch -> eval
private_memory_tune -> finetune
```

## Next step

Wire `api.data_rights_api.router` into `api.main` with:

```python
from api.data_rights_api import router as data_rights_router
app.include_router(data_rights_router)
```

Then add `data_source_id` to training job creation and reject jobs when the attached source does not allow that use.
