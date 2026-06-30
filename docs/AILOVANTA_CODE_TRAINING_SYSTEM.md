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
  autonomous GitHub source frontier discovery into source manifests

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

api/autonomous_code_training_loop.py
  autonomous code learning controller: discover/fetch/ingest/build tasks/run verification/export samples/train

api/code_failure_samples.py
  converts failed executable task runs into negative preference, repair, and reward-signal records

api/code_repair_loop.py
  generates repair candidates from failed task reports, re-runs verification, and exports accepted/rejected preference pairs

scripts/run_autonomous_code_training_loop.py
  one-command autonomous Ailovanta-Code loop

api/github_code_ingest.py
  corpus modes: instructions, code, mixed
```

Default ingest mode is `instructions` because writing code requires learning from requirements, tests, and docs. Use `--corpus-mode code` for foundation syntax/code modeling and `--corpus-mode mixed` for combined datasets.

## Commands

Discover broad GitHub sources:

```bash
python scripts/discover_github_sources.py \
  --output runtime_data/github_code_sources.json \
  --frontier runtime_data/github_source_frontier.json \
  --frontier-mode \
  --policy authorized_unrestricted
```

The GitHub source manifest is generated by the frontier. Operators do not need to enumerate every repository. The frontier persists query state, scores repositories, deduplicates by URL, expands language/topic queries from discovered repositories, and writes `runtime_data/github_code_sources.json` as the auditable ingest manifest.

Continuous full-auto training also writes `runtime_data/continuous_training_ledger.json`. This ledger records which source revision and corpus mode produced each dataset hash and training job. The next cycle syncs scheduler job status and skips already queued/completed fingerprints, so automatic crawling can run indefinitely without needing a human-maintained source list or repeatedly training the same code batch.

Candidate artifacts that fail the promotion gate write `runtime_data/candidate_failure_actions.json`. Model-quality and code-quality failures become `training_retrain` actions that the worker submits back into `/training/jobs`; storage/replica failures stay in the replica repair path. The current local code-quality gate requires code records, passing syntax checks, and a passing executable code-generation benchmark before a candidate can become active. This keeps automatic training moving after bad candidates instead of requiring manual triage.

The executable code-generation benchmark is the bridge from "trained artifact exists" to "trained artifact can write code." Supported local generative backends (`transformers-local` and `transformers-causal-lm`) are loaded from the artifact binding `backend_ref`. The gate prompts the model for small Python implementations, writes generated output into a temporary `solution.py`, and runs `python -m pytest` against task tests. The built-in `lightweight-ngram` backend cannot pass this benchmark and must remain a candidate/training proof, not a claimed code model.

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

Export failed task reports as negative/repair signals:

```bash
python scripts/export_failed_code_samples.py \
  runtime_data/code_task_reports.json \
  --output runtime_data/failed_code_samples.json
```

Failed samples contain:

```text
instruction
context files
candidate files that failed
stdout/stderr failure evidence
repair_prompt
training_use.positive_sft = false
training_use.negative_preference = true
training_use.repair_task = true
training_use.reward_signal = true
```

These records are for repair training, preference learning, ReST/RL reward signals, and diagnostics. They must not be mixed into positive SFT data.

Run failed task reports through the repair loop:

```bash
python scripts/run_code_repair_loop.py \
  runtime_data/code_task_reports.json \
  --output runtime_data/code_repair_results.json \
  --max-candidates-per-failure 16
```

Use the private core candidate generator while keeping public verification:

```bash
python scripts/run_code_repair_loop.py \
  runtime_data/code_task_reports.json \
  --output runtime_data/code_repair_results.json \
  --candidate-command "python ../ailovanta-core/scripts/generate_code_repair_candidates.py" \
  --backend-ref file://runtime_data/checkpoints/checkpoint.bin \
  --max-candidates-per-failure 16
```

The full autonomous loop can use the same bridge:

```bash
python scripts/run_autonomous_code_training_loop.py \
  --sources runtime_data/github_code_sources.json \
  --core-path ../ailovanta-core \
  --repair-candidate-command "python ../ailovanta-core/scripts/generate_code_repair_candidates.py" \
  --repair-backend-ref file://runtime_data/checkpoints/checkpoint.bin
```

If `--repair-backend-ref` is omitted, the autonomous loop reuses `runtime_data/autonomous_code_loop/latest_repair_backend_ref.json` when present. After a foundation run completes, the loop extracts the imported artifact `backend_ref` or `checkpoint_uri` and updates that file for the next run.

The repair loop:

```text
reads failed executable task reports
generates bounded repair candidate tasks locally or through private core
re-runs the same sandboxed verification commands
keeps only test-passing repairs as verified samples
exports chosen/rejected preference pairs for repair training and reward learning
```

The built-in candidate generator starts with deterministic Python operator mutations so the system can self-repair simple failing test/spec tasks without claiming a model solved them. The private core command uses the same external candidate protocol and can later switch from deterministic candidates to checkpoint/model-generated candidates. The gate remains the executable verifier.

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

## Autonomous Code Training Loop

Run the automatic code-learning loop:

```bash
python scripts/run_autonomous_code_training_loop.py \
  --sources runtime_data/github_code_sources.json \
  --core-path ../ailovanta-core \
  --max-sources 5 \
  --max-tasks 50
```

Run discovery first, then train:

```bash
python scripts/run_autonomous_code_training_loop.py \
  --discover \
  --max-sources 5 \
  --core-path ../ailovanta-core
```

The loop is intentionally stage-gated:

```text
source manifest / GitHub discovery
-> authorized fetch and rights proof
-> instruction-first corpus
-> executable test/spec tasks
-> sandboxed pytest/compile verification
-> verified_code_samples.json
-> failed_code_samples.json for negative/repair/reward signals
-> code_repair_results.json for auto-repair attempts and preference pairs
-> optional private core repair candidate command
-> repaired passing tasks merged back into verified_code_samples.json
-> foundation job
-> core checkpoint execution
-> public foundation import/runtime binding
-> latest_repair_backend_ref.json for the next repair round
-> run.json audit report
```

If no executable task passes, the loop can attempt bounded repairs. If repairs pass, the repaired candidates become verified samples and training can continue. If neither original tasks nor repairs pass, the loop stops at `no_verified_samples` and does not start training. This prevents the system from training on unverified or fake-positive code data.
