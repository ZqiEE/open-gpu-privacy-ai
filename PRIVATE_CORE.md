# Private Core Plan

The private core repository should hold the defensible system logic.

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

The public repository can reference these systems at a high level, but it should not contain their production implementation.

Suggested private repository name:

```text
open-gpu-privacy-ai-core
```

Suggested public repository purpose:

```text
open-gpu-privacy-ai-public
```
