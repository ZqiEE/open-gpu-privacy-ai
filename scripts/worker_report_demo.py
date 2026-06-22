from __future__ import annotations

import argparse
import json

from node_client.execution_report import build_execution_report
from node_client.job_runner import JobRunner
from node_client.report_store import ReportStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Create demo worker reports and save them locally")
    parser.add_argument("--db", default="runtime_data/worker_reports.sqlite3")
    args = parser.parse_args()

    runner = JobRunner()
    store = ReportStore(args.db)
    jobs = [
        {"id": "report_eval", "type": "evaluation", "payload": {"samples": 2}},
        {"id": "report_blocked", "type": "unknown_job", "payload": {}},
    ]
    for job in jobs:
        result = runner.run(job)
        report = build_execution_report("node_report_demo", job, result)
        saved = store.save(report)
        print(json.dumps(saved, ensure_ascii=False, indent=2))
    print("summary:", json.dumps(store.summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
