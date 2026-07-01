from api.testnet_v0 import run_testnet_v0_check


def test_testnet_v0_check_passes(tmp_path) -> None:
    result = run_testnet_v0_check(tmp_path)

    assert result["ok"] is True
    assert [item["name"] for item in result["checks"]] == [
        "start_gateway_api",
        "register_separate_node",
        "node_appears_in_nodes",
        "node_appears_in_runtime_nodes",
        "node_admission_check",
        "register_model_manifest",
        "runtime_route_assigns_capable_node",
        "submit_worker_result",
        "proof_verification_records_result",
        "build_artifact_chunk_manifest",
        "register_artifact_binding",
        "publish_owned_chat_route",
        "owned_chat_blocks_unpromoted_checkpoint",
        "owned_runtime_dashboard_reports_unready_chain",
    ]
    assert all(item["ok"] for item in result["checks"])
