# Rights Proof Registry

Rights Proof Registry records whether a data source can be used by Ailovanta training, distillation, evaluation, and runtime workflows.

Every code dataset and training job must bind to a `rights_id`.

## Record fields

```text
rights_id
provider_name
provider_type
agreement_id
agreement_uri
source_uri
source_type
license_name
allowed_uses
allowed_model_types
allowed_training_types
commercial_use_allowed
distillation_allowed
redistribution_allowed
expires_at
status
created_at
```

## Allowed uses

```text
inference
rag
finetune
pretrain
distillation
evaluation
benchmark
commercial_runtime
```

## Training rule

Training job creation must check that the record is active, the `rights_id` exists, and the requested training kind is listed in `allowed_training_types`.

For `code_distill`, the record must also set `distillation_allowed=true`.
