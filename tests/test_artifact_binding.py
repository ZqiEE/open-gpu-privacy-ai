from api.artifact_binding import ArtifactBindingStore


def test_artifact_binding_round_trip(tmp_path) -> None:
    store = ArtifactBindingStore(tmp_path / "bindings.sqlite3")
    runtime_model = {
        "model_id": "ailovanta-owned",
        "version": "candidate",
        "model_key": "ailovanta-owned:candidate",
        "manifest_hash": "sha256:runtime",
        "status": "active",
    }
    artifact = {
        "artifact_id": "artifact_1",
        "artifact_hash": "sha256:artifact",
        "checkpoint_uri": "artifact://plan/merged",
    }
    binding = store.register_binding(runtime_model, artifact)
    assert binding["model_key"] == "ailovanta-owned:candidate"
    assert binding["artifact_hash"] == "sha256:artifact"
    assert store.latest_for_model("ailovanta-owned:candidate")["binding_id"] == binding["binding_id"]
    updated = store.update_metadata(binding["binding_id"], {"gate": {"ok": True}})
    assert updated["metadata"]["gate"]["ok"] is True
    assert store.latest_for_model_statuses("ailovanta-owned:candidate", ("active",)) is None
    assert store.set_status(binding["binding_id"], "rolled_back")["status"] == "rolled_back"
