from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi.testclient import TestClient

from api.artifact_binding import ArtifactBindingStore
from api.chunk_manifest import build_manifest, sha256_bytes
from api.node_trust import NodeTrustStore
from api.parcel_store import ParcelStore
from api.runtime_forwarder import RuntimeEndpointStore
from api.route_book import RouteBook
from api.runtime_store import RuntimeStore
from api.storage import SchedulerStore
from api.wio import signed_result


def check_item(name: str, ok: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "details": details or {}}


@contextmanager
def isolated_runtime(work_dir: str | Path | None = None) -> Iterator[Path]:
    import api.main as main_module
    import api.wio_api as wio_module

    temp_dir = None
    if work_dir is None:
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
    else:
        root = Path(work_dir)
        root.mkdir(parents=True, exist_ok=True)

    original_store_path = main_module.store.path
    original_runtime_path = main_module.runtime_registry.path
    original_wio_store = wio_module.store
    original_trust_path = os.environ.get("AILOVANTA_NODE_TRUST_PATH")
    original_secrets = os.environ.get("AILOVANTA_NODE_SECRETS_JSON")
    original_require_owned = os.environ.get("AILOVANTA_REQUIRE_OWNED_MODEL")
    original_binding_path = os.environ.get("AILOVANTA_ARTIFACT_BINDINGS_PATH")
    original_route_book_path = os.environ.get("AILOVANTA_ROUTE_BOOK_PATH")
    original_endpoint_path = os.environ.get("AILOVANTA_RUNTIME_ENDPOINTS_PATH")
    original_validation_path = os.environ.get("AILOVANTA_WORKER_VALIDATION_PATH")
    original_reputation_path = os.environ.get("AILOVANTA_REPUTATION_PATH")
    try:
        main_module.store.path = SchedulerStore(root / "scheduler.sqlite3").path
        main_module.runtime_registry = RuntimeStore(root / "runtime.sqlite3")
        wio_module.store = ParcelStore(root / "parcels")
        os.environ["AILOVANTA_NODE_TRUST_PATH"] = str(root / "node_trust.sqlite3")
        os.environ["AILOVANTA_REQUIRE_OWNED_MODEL"] = "true"
        os.environ["AILOVANTA_ARTIFACT_BINDINGS_PATH"] = str(root / "artifact_bindings.sqlite3")
        os.environ["AILOVANTA_ROUTE_BOOK_PATH"] = str(root / "route_book.sqlite3")
        os.environ["AILOVANTA_RUNTIME_ENDPOINTS_PATH"] = str(root / "runtime_endpoints.json")
        os.environ["AILOVANTA_WORKER_VALIDATION_PATH"] = str(root / "worker_validations.sqlite3")
        os.environ["AILOVANTA_REPUTATION_PATH"] = str(root / "scheduler.sqlite3")
        yield root
    finally:
        main_module.store.path = original_store_path
        main_module.runtime_registry = RuntimeStore(original_runtime_path)
        wio_module.store = original_wio_store
        if original_trust_path is None:
            os.environ.pop("AILOVANTA_NODE_TRUST_PATH", None)
        else:
            os.environ["AILOVANTA_NODE_TRUST_PATH"] = original_trust_path
        if original_secrets is None:
            os.environ.pop("AILOVANTA_NODE_SECRETS_JSON", None)
        else:
            os.environ["AILOVANTA_NODE_SECRETS_JSON"] = original_secrets
        for key, value in {
            "AILOVANTA_REQUIRE_OWNED_MODEL": original_require_owned,
            "AILOVANTA_ARTIFACT_BINDINGS_PATH": original_binding_path,
            "AILOVANTA_ROUTE_BOOK_PATH": original_route_book_path,
            "AILOVANTA_RUNTIME_ENDPOINTS_PATH": original_endpoint_path,
            "AILOVANTA_WORKER_VALIDATION_PATH": original_validation_path,
            "AILOVANTA_REPUTATION_PATH": original_reputation_path,
        }.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if temp_dir is not None:
            temp_dir.cleanup()


def run_testnet_v0_check(work_dir: str | Path | None = None) -> dict[str, Any]:
    from api.main_learning import app

    node_id = "node-testnet-v0"
    runtime_id = "rt-testnet-v0"
    model_id = "ailovanta-testnet"
    version = "v0"
    model_key = f"{model_id}:{version}"
    secret = "testnet-v0-secret"

    checks: list[dict[str, Any]] = []
    with isolated_runtime(work_dir) as root:
        client = TestClient(app)
        NodeTrustStore().register(node_id, secret, trust_score=0.9)
        os.environ["AILOVANTA_NODE_SECRETS_JSON"] = json.dumps({node_id: secret})
        RuntimeEndpointStore(root / "runtime_endpoints.json").register(runtime_id, "inprocess://ailovanta-worker")

        root_response = client.get("/")
        checks.append(check_item("start_gateway_api", root_response.status_code == 200, {"status_code": root_response.status_code}))

        node_response = client.post(
            "/nodes/register",
            json={
                "node_id": node_id,
                "device_name": "testnet-v0-node",
                "cpu_threads": 8,
                "memory_gb": 16,
                "has_gpu": True,
                "gpu_name": "testnet-gpu",
                "contribution_percent": 30,
            },
        )
        checks.append(check_item("register_separate_node", node_response.status_code == 200, node_response.json() if node_response.status_code == 200 else {"status_code": node_response.status_code}))

        nodes = client.get("/nodes").json().get("nodes", [])
        checks.append(check_item("node_appears_in_nodes", any(item.get("node_id") == node_id for item in nodes), {"node_count": len(nodes)}))

        runtime_payload = {
            "runtime_id": runtime_id,
            "node_id": node_id,
            "pool": "trusted_runtime_pool",
            "region": "global",
            "status": "online",
            "gpu_memory_gb": 24,
            "available_gpu_memory_gb": 20,
            "trust_score": 0.9,
            "current_load": 0.1,
            "price_per_1k_tokens": 0.0,
            "latency_ms": 100,
            "supported_engines": ["python", "local"],
            "cached_models": [model_key],
            "cached_adapters": [],
        }
        runtime_response = client.post("/runtime/nodes/register", json=runtime_payload)
        runtime_nodes = client.get("/runtime/nodes").json().get("nodes", [])
        checks.append(check_item("node_appears_in_runtime_nodes", runtime_response.status_code == 200 and any(item.get("runtime_id") == runtime_id for item in runtime_nodes), {"runtime_node_count": len(runtime_nodes)}))

        admission = client.post("/node-admission/check", json={"node": runtime_payload})
        admission_body = admission.json()
        checks.append(check_item("node_admission_check", admission.status_code == 200 and admission_body.get("ok") is True, admission_body))

        model_response = client.post(
            "/runtime/models/register",
            json={
                "model_id": model_id,
                "version": version,
                "manifest_hash": "sha256:testnetv0model",
                "privacy_level": "protected",
                "min_gpu_memory_gb": 0,
                "allowed_pools": ["trusted_runtime_pool"],
                "quantization": "local",
                "context_length": 2048,
            },
        )
        checks.append(check_item("register_model_manifest", model_response.status_code == 200, model_response.json() if model_response.status_code == 200 else {"status_code": model_response.status_code}))

        route = client.post(
            "/runtime/route",
            json={
                "request_id": "req-testnet-v0",
                "model_id": model_id,
                "version": version,
                "task_type": "chat_completion",
                "privacy_level": "protected",
                "latency_target_ms": 1000,
                "max_price_per_1k_tokens": 0.01,
                "region_hint": "global",
                "verification_required": True,
            },
        )
        route_body = route.json()
        checks.append(check_item("runtime_route_assigns_capable_node", route.status_code == 200 and route_body.get("assigned") is True and route_body.get("assignment", {}).get("runtime_id") == runtime_id, route_body))

        task = client.post(
            "/wio/task",
            json={
                "plan": {"plan_id": "plan-testnet-v0", "max_steps": 1, "estimated_total_tokens": 8},
                "node_id": node_id,
                "input_uri": "file://runtime_data/testnet-v0-input.jsonl",
                "output_uri": "file://runtime_data/testnet-v0-output.bin",
            },
        ).json()["item"]["task"]
        checkpoint_bytes = b"testnet-v0-checkpoint"
        checkpoint_hash = sha256_bytes(checkpoint_bytes)
        result_payload = signed_result(
            {
                "task_id": task["task_id"],
                "checkpoint_uri": "file://" + str(root / "checkpoint.bin"),
                "checkpoint_hash": checkpoint_hash,
                "token_count": 8,
                "train_loss": 0.1,
                "eval_loss": 0.2,
            },
            node_id=node_id,
            secret=secret,
        )
        result_response = client.post("/wio/result", json={"payload": result_payload, "require_valid": True})
        checks.append(check_item("submit_worker_result", result_response.status_code == 200, result_response.json() if result_response.status_code == 200 else {"status_code": result_response.status_code, "body": result_response.text}))

        results = client.get("/wio/results").json().get("results", [])
        proof_recorded = bool(results) and result_response.status_code == 200 and result_response.json().get("checked", {}).get("ok") is True
        checks.append(check_item("proof_verification_records_result", proof_recorded, {"result_count": len(results), "checked": result_response.json().get("checked") if result_response.status_code == 200 else None}))

        artifact_path = root / "checkpoint.bin"
        artifact_path.write_bytes(checkpoint_bytes)
        manifest = build_manifest(artifact_path, chunk_size=8, sources=[f"node://{node_id}/checkpoint.bin"], min_replicas=1)
        checks.append(check_item("build_artifact_chunk_manifest", manifest.get("artifact_hash") == checkpoint_hash and len(manifest.get("chunks") or []) >= 1, manifest))

        binding = ArtifactBindingStore(root / "artifact_bindings.sqlite3").register_binding(
            {
                "model_id": model_id,
                "version": version,
                "model_key": model_key,
                "manifest_hash": "sha256:testnetv0model",
                "status": "active",
            },
            {
                "artifact_id": manifest["artifact_id"],
                "artifact_hash": manifest["artifact_hash"],
                "checkpoint_uri": "file://" + str(artifact_path),
            },
            backend_kind="checkpoint-artifact",
            backend_ref="file://" + str(artifact_path),
            status="active",
            metadata={"artifact_manifest": manifest},
        )
        checks.append(check_item("register_artifact_binding", binding.get("runtime_manifest_hash") == "sha256:testnetv0model" and binding.get("status") == "active", binding))
        owned_route = RouteBook(root / "route_book.sqlite3").set_active(
            "owned-chat/default",
            model_key,
            binding_id=binding["binding_id"],
            reason="testnet_v0_artifact_binding_ready",
            metadata={"runtime_id": runtime_id, "node_id": node_id, "artifact_hash": binding["artifact_hash"]},
        )
        checks.append(check_item("publish_owned_chat_route", owned_route.get("binding_id") == binding["binding_id"] and owned_route.get("status") == "active", owned_route))

        chat_response = client.post("/ailovanta/v1/chat", json={"prompt": "test owned chat", "model_id": model_id, "version": version})
        chat_body = chat_response.json()
        checks.append(
            check_item(
                "owned_chat_blocks_unpromoted_checkpoint",
                chat_response.status_code == 200
                and chat_body.get("owned_model_ready") is False
                and chat_body.get("self_trained_ready") is False
                and chat_body.get("source") == "owned-runtime-unavailable"
                and chat_body.get("model_readiness", {}).get("stage") == "bootstrap_connected",
                chat_body,
            )
        )

        dashboard = client.get("/dashboard/owned-runtime")
        dashboard_body = dashboard.json()
        checks.append(
            check_item(
                "owned_runtime_dashboard_reports_unready_chain",
                dashboard.status_code == 200
                and dashboard_body.get("ok") is False
                and "worker_validation_receipt_missing" in dashboard_body.get("blockers", [])
                and dashboard_body.get("model_readiness", {}).get("self_trained_ready") is False,
                dashboard_body,
            )
        )

    return {"ok": all(item["ok"] for item in checks), "checks": checks}
