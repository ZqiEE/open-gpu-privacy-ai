from __future__ import annotations

import argparse
import json

from api.contribution_ledger import ContributionLedger
from api.model_commit_registry import ModelCommitRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description="Print decentralized ledger report")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--node-id", default=None)
    args = parser.parse_args()
    ledger = ContributionLedger()
    models = ModelCommitRegistry()
    report = {
        "network": ledger.network_summary(),
        "node": ledger.node_summary(args.node_id) if args.node_id else None,
        "events": ledger.list_events(node_id=args.node_id, limit=args.limit),
        "model_commits": models.list_commits(limit=args.limit),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
