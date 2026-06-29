# Ailovanta-Code Training System

## Goal

Ailovanta-Code should learn to write, repair, explain, and maintain software across languages and repositories.

GitHub-scale ingestion is the discovery layer. The training system must not treat raw finished code as the only learning signal.

## Three-layer Learning Stack

```text
Layer 1: language foundation
-> spelling, tokens, grammar, AST shape, syntax errors, type systems, module systems, standard libraries, framework APIs

Layer 2: engineering structure
-> repository layout, dependency files, build systems, tests, CI, lint, security patterns, framework conventions

Layer 3: task execution
-> requirements, issue triage, test-driven implementation, bug fixing, refactoring, PR explanation, CI repair
```

Raw source code is necessary for layer 1 and context. It teaches syntax, identifiers, library usage, and code style.

Instruction-first data is necessary for layer 3. It teaches how to turn requirements, docs, tests, bugs, and error logs into working changes.

## GitHub-scale Source Discovery

Broad GitHub discovery should collect repository candidates from:

```text
GitHub search queries
language/topic/star/activity filters
organization allowlists
operator-provided source manifests
fork and duplicate detection
quality scoring
```

Personal/operator-authorized mode can use broad policies:

```text
private_owner_unrestricted
authorized_unrestricted
shareholder_authorized
explicit_permission
internal
```

Public/shared mode should still record a source policy and rights proof. It can be broad, but it must remain auditable:

```text
source URI
commit SHA
rights_id
authorization basis
training uses
commercial/distillation flags
content hashes
secret scan status
```

## Data Types

The crawler should extract multiple datasets from each repository:

```text
raw_code
  source files for syntax, APIs, project structure, idioms

docs
  README, docs, architecture notes, API guides, examples

tests
  unit tests, integration tests, specs, snapshots, expected behavior

issues_prs
  issue titles/bodies, PR descriptions, review comments, labels

diffs_commits
  commit messages, changed files, patch hunks, before/after pairs

ci_logs
  failing jobs, stack traces, compiler errors, lint/typecheck output
```

## Training Dataset Construction

Mature code training should build several sample families:

```text
grammar/code modeling
  input: raw code
  target: next tokens / infill / AST-consistent completion

doc-to-code
  input: README/API docs + repository context
  target: implementation or usage example

test-to-code
  input: tests/specs + relevant context
  target: implementation that passes tests

issue-to-patch
  input: issue/bug report + repository context
  target: patch

error-to-fix
  input: stack trace / CI log / compiler error
  target: diagnosis + patch

diff explanation
  input: patch
  target: explanation, risk analysis, test plan
```

## Algorithms

The system should use a staged algorithm, not one flat corpus:

```text
1. Discover repositories
2. Score repository quality
3. Clone/fetch selected repositories
4. Filter secrets, generated files, vendored dependencies, duplicates
5. Extract raw code foundation records
6. Extract instruction-first records from docs/tests/issues/diffs/logs
7. Generate candidate solutions for executable tasks
8. Run tests/lint/typecheck/compile
9. Keep validated samples and discard failed or poisoned samples
10. Train with SFT/distillation/ReST/RL using test outcomes as reward
11. Evaluate on held-out repo tasks and benchmarks
12. Promote only when gates improve
```

## Model Training Phases

```text
Phase A: foundation code modeling
  large multilingual raw code corpus
  objective: syntax, spelling, APIs, style, structure

Phase B: instruction SFT
  docs/tests/issues/PR-derived tasks
  objective: follow requirements and produce useful code

Phase C: verified distillation
  multiple candidates -> run tests -> keep best passing answer
  objective: reliable code generation and repair

Phase D: reinforcement from execution
  reward: test_pass_rate, patch_apply_rate, typecheck/lint success, CI repair success
  objective: improve real task success

Phase E: repo-level RAG runtime
  retrieve current repo docs/tests/source before answering
  objective: avoid memorizing every repo into weights
```

## Current Implementation Direction

The current public repo now supports:

```text
scripts/discover_github_sources.py
  broad GitHub repository discovery into source manifests

scripts/ingest_github_code.py
  authorized source ingest, rights proof creation, corpus creation, optional code training job

api/code_instruction_data.py
  instruction-first records from README/docs/tests/specs/templates

api/code_task_builder.py
  converts instruction records into executable worker code tasks

node_client/code_task_runner.py
  runs allowlisted compile/test commands in a temporary sandbox

api/verified_code_samples.py
  converts passed code task reports into training-ready verified samples

api/verified_code_foundation.py
  converts verified code samples into a core foundation job dataset

scripts/run_verified_code_foundation.py
  one-command bridge from verified code samples to local core checkpoint artifact

api/github_code_ingest.py
  corpus modes: instructions, code, mixed
```

Default ingest mode is `instructions` because writing code requires learning from requirements, tests, and docs. Use `--corpus-mode code` for foundation syntax/code modeling and `--corpus-mode mixed` for combined datasets.

## Commands

Discover broad GitHub sources:

```bash
python scripts/discover_github_sources.py \
  --output runtime_data/github_code_sources.json \
  --query "stars:>=500 language:Python archived:false" \
  --policy authorized_unrestricted
```

Build instruction-first data and a distributed training job:

```bash
python scripts/ingest_github_code.py \
  --sources runtime_data/github_code_sources.json \
  --corpus-mode instructions \
  --create-job
```

Build raw code foundation data:

```bash
python scripts/ingest_github_code.py \
  --sources runtime_data/github_code_sources.json \
  --corpus-mode code
```

Build combined data:

```bash
python scripts/ingest_github_code.py \
  --sources runtime_data/github_code_sources.json \
  --corpus-mode mixed \
  --create-job
```

Convert instruction data into executable worker tasks:

```bash
python scripts/build_code_instruction_tasks.py \
  runtime_data/code_corpus_github.jsonl \
  --output runtime_data/code_instruction_tasks.json
```

Current executable task support is intentionally controlled:

```text
task_type = code_instruction_eval
worker writes task files into a temporary sandbox
allowed commands: python -m py_compile, python -m pytest
all command output is captured into a verified run report
unknown shell commands are rejected
```

This is the bridge from instruction-first data to test-verified training samples.

Export passed task reports as verified training samples:

```bash
python scripts/export_verified_code_samples.py \
  runtime_data/code_task_reports.json \
  --output runtime_data/verified_code_samples.json
```

Verified samples contain:

```text
instruction
context files
candidate files / patch material
verification commands
report hash
sample hash
```

Only passing reports become samples. Failed reports stay useful for diagnostics and RL negative signals, but they are not exported as positive SFT/distillation examples by default.

Run verified samples through the owned foundation pipeline:

```bash
python scripts/run_verified_code_foundation.py \
  runtime_data/verified_code_samples.json \
  --core-path ../ailovanta-core \
  --work-dir runtime_data/verified_code_foundation \
  --output runtime_data/verified_code_foundation/pipeline_result.json
```

This creates:

```text
verified_code_samples.json
-> verified_code_sft JSONL dataset
-> ailovanta.foundation_job.v1
-> ailovanta-core run_foundation_job.py
-> local checkpoint execution by default
-> foundation_result.json
-> public runtime import / artifact binding
```

Use `--simulate` when the machine should only plan the job without local checkpoint execution. Use `--training-command` to replace the default local trainer with a stronger backend command.
