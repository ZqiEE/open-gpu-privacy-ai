# Code Distillation

Ailovanta-Code should use distillation as a verifiable code capability pipeline.

## Sources

Allowed distillation sources include:

- authorized teacher outputs
- open-source teacher outputs
- user-confirmed useful answers
- automatically test-passing code
- multi-candidate answers
- successful CI fix records
- merged pull request records

## Flow

```text
generate multiple candidates
-> run tests
-> run lint
-> run typecheck
-> run quality checks
-> choose the strongest passing answer
-> write distilled_code samples
-> distributed training of Ailovanta-Code adapter
```

## Metrics

Core metrics:

- test_pass_rate
- patch_apply_rate
- ci_fix_success_rate
- lint_success_rate
- typecheck_success_rate
- regression_rate
- quality_warning_rate

Distillation must not be represented as copying a closed model. It is a controlled, rights-bound, validation-first training path.
