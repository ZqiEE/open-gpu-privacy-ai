from __future__ import annotations

import json
import os
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from api.code_task_builder import load_instruction_records, task_from_instruction_record
from api.code_failure_samples import export_failures_from_reports
from api.code_repair_loop import repair_failures_from_reports
from api.foundation_pipeline import run_foundation_pipeline
from api.github_code_ingest import ingest_sources
from api.verified_code_foundation import create_job_from_verified_code_export
from api.verified_code_samples import export_samples_from_reports
from node_client.code_task_runner import run_code_instruction_task


class AutonomousCodeTrainingLoop:
    """Runs Ailovanta-Code's self-learning path from sources to verified training."""

    def __init__(self, core_path: str | Path | None = None, root: str | Path = "runtime_data/autonomous_code_loop") -> None:
        self.core_root = Path(core_path or os.getenv("AILOVANTA_CORE_PATH", "../ailovanta-core")).resolve()
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def run_once(
        self,
        sources_path: str | Path = "runtime_data/github_code_sources.json",
        discover: bool = False,
        fetch: bool = True,
        corpus_mode: str = "instructions",
        max_sources: int | None = None,
        max_tasks: int = 50,
        max_candidate_files: int = 64,
        run_foundation: bool = True,
        execute_checkpoints: bool = True,
        model_id: str = "ailovanta-code",
        target_version: str = "candidate",
        max_steps: int = 100,
        work_dir: str | Path | None = None,
        training_command: str | None = None,
        repair_failures: bool = True,
        max_repair_candidates: int = 16,
        repair_candidate_command: str | None = None,
        repair_backend_ref: str | None = None,
    ) -> dict[str, Any]:
        run_id = "auto_code_" + uuid4().hex[:12]
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        source_manifest = Path(sources_path)
        discovery = self._maybe_discover(source_manifest, enabled=discover)
        prepared_sources = self._limit_sources(source_manifest, run_dir / "sources.json", max_sources=max_sources)
        corpus_path = run_dir / "code_corpus.jsonl"
        ingest = ingest_sources(
            prepared_sources,
            target_root=run_dir / "source_repos",
            corpus_output=corpus_path,
            rights_path=run_dir / "rights_proofs.json",
            jobs_path=run_dir / "code_training_jobs.json",
            fetch=fetch,
            create_job=False,
            corpus_mode=corpus_mode,
        )
        records = load_instruction_records(corpus_path, limit=max_tasks)
        task_items = self._build_tasks(records, max_candidate_files=max_candidate_files)
        task_path = run_dir / "code_instruction_tasks.json"
        task_path.write_text(json.dumps({"schema_version": "ailovanta.code_instruction_tasks.v1", "tasks": task_items}, ensure_ascii=False, indent=2), encoding="utf-8")

        report_items = []
        for task in task_items:
            run = run_code_instruction_task(task)
            report_items.append({"task": task, "report": run.report})
        reports_path = run_dir / "code_task_reports.json"
        reports_path.write_text(json.dumps({"schema_version": "ailovanta.code_task_reports.v1", "items": report_items}, ensure_ascii=False, indent=2), encoding="utf-8")

        failures_path = run_dir / "failed_code_samples.json"
        failures = export_failures_from_reports(report_items, failures_path)
        repairs_path = run_dir / "code_repair_results.json"
        repairs = (
            repair_failures_from_reports(
                report_items,
                repairs_path,
                max_candidates_per_failure=max_repair_candidates,
                candidate_command=repair_candidate_command,
                backend_ref=repair_backend_ref,
            )
            if repair_failures
            else self._write_empty_repairs(repairs_path)
        )
        verified_report_items = report_items + repairs.get("verified_report_items", [])
        repaired_reports_path = run_dir / "code_task_reports_with_repairs.json"
        repaired_reports_path.write_text(json.dumps({"schema_version": "ailovanta.code_task_reports.v1", "items": verified_report_items}, ensure_ascii=False, indent=2), encoding="utf-8")
        verified_path = run_dir / "verified_code_samples.json"
        verified = export_samples_from_reports(verified_report_items, verified_path)
        foundation = None
        stage = "verified_samples_ready"
        ok = bool(verified.get("count"))
        if run_foundation and ok:
            if not self.core_root.exists():
                raise ValueError("ailovanta-core path not found: " + str(self.core_root))
            job = create_job_from_verified_code_export(
                verified_path,
                model_id=model_id,
                target_version=target_version,
                max_steps=max_steps,
                execute_checkpoints=execute_checkpoints,
                dataset_output_dir=run_dir / "verified_code_datasets",
            )
            pipeline = run_foundation_pipeline(
                job["job_id"],
                core_path=self.core_root,
                work_dir=work_dir or (run_dir / "foundation_pipeline"),
                execute_checkpoints=execute_checkpoints,
                checkpoint_output_root=run_dir / "checkpoints",
                training_command=training_command,
            )
            foundation = {"job": job, "pipeline": pipeline}
            stage = "foundation_pipeline_complete"
        elif not ok:
            stage = "no_verified_samples"

        payload = {
            "schema_version": "ailovanta.autonomous_code_training_run.v1",
            "run_id": run_id,
            "ok": ok and (foundation is not None if run_foundation else True),
            "stage": stage,
            "paths": {
                "run_dir": str(run_dir),
                "sources": str(prepared_sources),
                "corpus": str(corpus_path),
                "tasks": str(task_path),
                "reports": str(reports_path),
                "reports_with_repairs": str(repaired_reports_path),
                "verified_samples": str(verified_path),
                "failed_samples": str(failures_path),
                "repairs": str(repairs_path),
            },
            "discovery": discovery,
            "ingest": self._compact_ingest(ingest),
            "records": len(records),
            "tasks": len(task_items),
            "task_results": {
                "passed": len([item for item in report_items if item["report"].get("passed")]),
                "failed": len([item for item in report_items if not item["report"].get("passed")]),
            },
            "verified": {key: value for key, value in verified.items() if key != "samples"},
            "failures": {key: value for key, value in failures.items() if key != "samples"},
            "repairs": {key: value for key, value in repairs.items() if key not in {"attempts", "preference_pairs", "verified_report_items"}},
            "foundation": foundation,
            "created_at": round(time(), 3),
        }
        self._write_run(payload)
        return payload

    def latest_run(self) -> dict[str, Any] | None:
        rows = sorted(self.runs_dir.glob("*/run.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return json.loads(rows[0].read_text(encoding="utf-8")) if rows else None

    def list_runs(self) -> list[dict[str, Any]]:
        return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(self.runs_dir.glob("*/run.json"))]

    def _write_run(self, payload: dict[str, Any]) -> None:
        run_dir = self.runs_dir / payload["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _maybe_discover(self, output_path: Path, enabled: bool) -> dict[str, Any]:
        if not enabled:
            return {"ok": True, "enabled": False, "output": str(output_path)}
        from scripts.discover_github_sources import DEFAULT_QUERIES, load_manifest, save_manifest, search_repositories, source_from_repo, upsert_sources

        token = os.getenv("GITHUB_TOKEN")
        manifest = load_manifest(output_path)
        discovered = []
        for query in DEFAULT_QUERIES:
            repos = search_repositories(query, pages=1, per_page=20, token=token)
            discovered.extend(source_from_repo(repo, "authorized_unrestricted", "operator authorized autonomous GitHub code learning") for repo in repos)
        added = upsert_sources(manifest, discovered)
        save_manifest(output_path, manifest)
        return {"ok": True, "enabled": True, "queries": DEFAULT_QUERIES, "discovered": len(discovered), "added": added, "output": str(output_path)}

    def _limit_sources(self, source_manifest: Path, output_path: Path, max_sources: int | None) -> Path:
        payload = json.loads(source_manifest.read_text(encoding="utf-8-sig"))
        sources = payload.get("sources", [])
        if max_sources is not None:
            payload = {**payload, "sources": sources[:max_sources]}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _build_tasks(self, records: list[dict[str, Any]], max_candidate_files: int) -> list[dict[str, Any]]:
        tasks = []
        for record in records:
            if record.get("record_type") != "test_spec":
                continue
            candidates = candidate_files_for_record(record, max_files=max_candidate_files)
            task = task_from_instruction_record(record, candidate_files=candidates)
            if task["payload"].get("commands"):
                tasks.append(task)
        return tasks

    @staticmethod
    def _compact_ingest(ingest: dict[str, Any]) -> dict[str, Any]:
        keys = ["ok", "sources", "accepted_sources", "records", "bytes", "languages", "corpus_output", "rights_path", "corpus_mode"]
        return {key: ingest.get(key) for key in keys}

    @staticmethod
    def _write_empty_repairs(output_path: Path) -> dict[str, Any]:
        payload = {
            "schema_version": "ailovanta.code_repair_export.v1",
            "failed_tasks": 0,
            "attempted_repairs": 0,
            "repaired": 0,
            "attempts": [],
            "preference_pairs": [],
            "created_at": round(time(), 3),
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "failed_tasks": 0, "attempted_repairs": 0, "repaired": 0, "output_path": str(output_path), "verified_report_items": []}


def candidate_files_for_record(record: dict[str, Any], max_files: int = 64, max_file_bytes: int = 256_000) -> dict[str, str]:
    root = Path(str(record.get("source_root") or "")).resolve()
    source_path = str(record.get("path") or "")
    if not root.exists():
        return {}
    candidates: dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        rel = str(path.resolve().relative_to(root))
        rel_lower = rel.lower().replace("\\", "/")
        if rel == source_path or "/test" in rel_lower or rel_lower.startswith("test") or "__pycache__" in rel_lower:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
            candidates[rel] = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(candidates) >= max_files:
            break
    return candidates
