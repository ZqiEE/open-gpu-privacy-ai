from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from api.alert_summary import AlertSummary
from api.incident_response import IncidentResponse
from api.prod_ready_plus import check_production_ready_plus
from api.route_health import RouteHealth
from api.runtime_readiness import RuntimeReadiness


def run_cmd(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def release_gate(core_path: str = "../ailovanta-core", result_path: str | None = None, route_key: str = "owned-chat/default", run_tests: bool = True, verify_bytes: bool = False, verify_distribution: bool = False, verify_chain: bool = False) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    blockers: list[str] = []

    if run_tests:
        checks["pytest"] = run_cmd([sys.executable, "-m", "pytest", "-q"])
        if not checks["pytest"].get("ok"):
            blockers.append("pytest_failed")

    checks["validate"] = run_cmd([sys.executable, "validate.py"])
    if not checks["validate"].get("ok"):
        blockers.append("validate_failed")

    checks["preflight"] = run_cmd([sys.executable, "scripts/preflight.py", "--core-path", core_path])
    if not checks["preflight"].get("ok"):
        blockers.append("preflight_failed")

    result_exists = bool(result_path and Path(result_path).exists())
    checks["prod_ready_plus"] = check_production_ready_plus(result_path=result_path if result_exists else None, route_key=route_key, verify_bytes=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
    if not checks["prod_ready_plus"].get("ok"):
        blockers.extend("prod_ready_plus:" + str(item) for item in checks["prod_ready_plus"].get("blockers", []))

    checks["route_health"] = RouteHealth().check(route_key, verify_artifact=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
    if not checks["route_health"].get("ok"):
        blockers.extend("route_health:" + str(item) for item in checks["route_health"].get("blockers", []))

    checks["runtime_route"] = RuntimeReadiness().check_route(route_key)
    if not checks["runtime_route"].get("ok"):
        blockers.append("runtime_route:" + str(checks["runtime_route"].get("reason")))

    checks["alerts"] = AlertSummary().collect(route_key=route_key, verify_bytes=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain)
    if not checks["alerts"].get("ok"):
        for item in checks["alerts"].get("alerts", []):
            if item.get("severity") in {"critical", "high"}:
                blockers.append("alert:" + str(item.get("source")) + ":" + str(item.get("message")))

    checks["incident_dry_run"] = IncidentResponse().execute(route_key=route_key, verify_bytes=verify_bytes, verify_distribution=verify_distribution, verify_chain=verify_chain, dry_run=True)
    if not checks["incident_dry_run"].get("ok"):
        blockers.append("incident_dry_run_failed")

    return {
        "ok": not blockers,
        "stage": "release_pass" if not blockers else "release_blocked",
        "blockers": sorted(set(blockers)),
        "checks": checks,
    }
