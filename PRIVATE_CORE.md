# Ailovanta Private Core Plan

Ailovanta's private core repository should hold the defensible system logic.

Move private development into a separate private repository before adding production details.

Private core should contain:

- production router logic
- production validator logic
- production scoring logic
- production abuse detection
- production node trust rules
- model package builder internals
- protected runtime internals
- production deployment scripts
- operator workflows
- sensitive configuration templates
- H-SwarmTrain orchestration modules

The public repository can reference these systems at a high level, but it should not contain their production implementation.

Current private repository:

```text
https://github.com/ZqiEE/ailovanta-core.git
```

Public repository:

```text
https://github.com/ZqiEE/ailovanta.git
```

Public brand:

```text
Ailovanta
```
