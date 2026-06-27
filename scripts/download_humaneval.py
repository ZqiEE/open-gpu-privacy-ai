from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from urllib.request import urlopen

DEFAULT_URL = "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz"


def download(url: str, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = output.with_suffix(output.suffix + ".gz") if not str(output).endswith(".gz") else output
    with urlopen(url, timeout=120) as response, raw.open("wb") as handle:
        handle.write(response.read())
    if str(raw).endswith(".gz"):
        target = output if not str(output).endswith(".gz") else output.with_suffix("")
        with gzip.open(raw, "rt", encoding="utf-8") as source, target.open("w", encoding="utf-8") as dest:
            count = 0
            for line in source:
                item = json.loads(line)
                dest.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
        return {"ok": True, "source": url, "gz_path": str(raw), "jsonl_path": str(target), "tasks": count}
    count = sum(1 for _ in raw.open("r", encoding="utf-8"))
    return {"ok": True, "source": url, "jsonl_path": str(raw), "tasks": count}


def main() -> int:
    parser = argparse.ArgumentParser(description="Download HumanEval JSONL for local benchmark use")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", default="runtime_data/benchmarks/HumanEval.jsonl")
    args = parser.parse_args()
    print(json.dumps(download(args.url, Path(args.output)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
