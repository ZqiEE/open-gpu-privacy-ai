from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.github_code_ingest import ingest_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest authorized GitHub/code sources into code corpus, rights proof, and optional training jobs")
    parser.add_argument("--sources", default="runtime_data/github_code_sources.json")
    parser.add_argument("--target-root", default="runtime_data/source_repos")
    parser.add_argument("--corpus-output", default="runtime_data/code_corpus_github.jsonl")
    parser.add_argument("--rights-path", default="runtime_data/rights_proofs.json")
    parser.add_argument("--jobs-path", default="runtime_data/code_training_jobs.json")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--create-job", action="store_true")
    parser.add_argument("--training-kind", default="code_lora")
    parser.add_argument("--max-file-bytes", type=int, default=512_000)
    parser.add_argument("--corpus-mode", choices=["instructions", "code", "mixed"], default="instructions")
    args = parser.parse_args()
    result = ingest_sources(
        args.sources,
        target_root=args.target_root,
        corpus_output=args.corpus_output,
        rights_path=args.rights_path,
        jobs_path=args.jobs_path,
        fetch=not args.no_fetch,
        create_job=args.create_job,
        training_kind=args.training_kind,
        max_file_bytes=args.max_file_bytes,
        corpus_mode=args.corpus_mode,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
