from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.contribution_ledger import ContributionLedger
from api.model_commit_registry import ModelCommitRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description="Export local ledger records for chain adapters")
    parser.add_argument("--output", default="runtime_data/ledger_chain_export.json")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    ledger = ContributionLedger()
    models = ModelCommitRegistry()
    payload = {
        "network": ledger.network_summary(),
        "events": ledger.list_events(limit=args.limit),
        "model_commits": models.list_commits(limit=args.limit),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
