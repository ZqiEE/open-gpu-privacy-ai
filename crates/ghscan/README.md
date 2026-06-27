# ghscan

Rust GitHub discovery and sync tool for Ailovanta-Code.

It searches public GitHub repositories by rules, syncs matching repositories with git, and writes `runtime_data/input_list.json` for the existing Python dataset builder.

## Build

```bash
cargo build -p ghscan
```

## Run

```bash
export GITHUB_TOKEN=your_token
cargo run -p ghscan -- \
  --languages python,typescript,javascript,rust,go \
  --licenses mit,apache-2.0,bsd-3-clause,bsd-2-clause,isc \
  --min-stars 20 \
  --pushed-after 2024-01-01 \
  --pages-per-query 2 \
  --per-page 50 \
  --cache-dir runtime_data/input_cache \
  --out runtime_data/input_list.json
```

## Output

Each synced repository becomes an item with:

```json
{
  "repo_id": "owner_repo",
  "repo_url": "https://github.com/owner/repo",
  "rights_id": "github_public_permissive_v1",
  "status": "active",
  "local_path": "runtime_data/input_cache/owner_repo",
  "license": "mit",
  "language": "Python",
  "stars": 100
}
```

Then build the JSONL pack:

```bash
python - <<'PY'
from api.input_list import InputList
from api.builder import build_pack
items = InputList('runtime_data/input_list.json').read()
print(build_pack(items, 'runtime_data/code_pack.jsonl'))
PY
```
