from api.owned_entry import CheckedOwnedChatRequest, checked_owned_chat


class DummyRegistry:
    def route(self, request):
        return {"assigned": True, "assignment": {"runtime_id": "rt", "node_id": "node", "model_manifest_hash": "sha256:r"}}


def test_checked_owned_chat_rejects_without_binding(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_ARTIFACT_BINDINGS_PATH", str(tmp_path / "artifact_bindings.sqlite3"))
    result = checked_owned_chat(CheckedOwnedChatRequest(prompt="hello"), DummyRegistry())
    assert result["ok"] is False
    assert result["owned_model_ready"] is False
    assert result["route_policy"]["reason"] == "no usable model binding"
