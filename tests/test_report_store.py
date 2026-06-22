from __future__ import annotations

import tempfile
from pathlib import Path

from node_client.execution_report import build_execution_report
from node_client.job_runner import JobRunner
from node_client.report_store import ReportStore


def test_report_store_saves_and_lists_reports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ReportStore(Path(tmp) / "reports.sqlite3")
        runner = JobRunner()
        job = {"id": "report_store_job", "type": "verification", "payload": {"samples": 1}}
        result = runner.run(job)
        report = build_execution_report("node_store", job, result)
        saved = store.save(report)
        assert saved["report_id"] == report["report_id"]
        assert saved["descriptor_ok"] is True
        reports = store.list_reports(node_id="node_store")
        assert len(reports) == 1


def test_report_store_summary_counts_status() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = ReportStore(Path(tmp) / "reports.sqlite3")
        runner = JobRunner()
        ok_job = {"id": "ok_job", "type": "verification", "payload": {"samples": 1}}
        bad_job = {"id": "bad_job", "type": "blocked", "payload": {}}
        store.save(build_execution_report("node_store", ok_job, runner.run(ok_job)))
        store.save(build_execution_report("node_store", bad_job, runner.run(bad_job)))
        summary = store.summary()
        assert summary["total_reports"] == 2
        assert summary["ok_reports"] == 1
        assert summary["failed_reports"] == 1
