from api.worker_transport import WorkerInferenceClient, WorkerInferenceUnavailable


def test_worker_url_uses_specific_env(monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_WORKER_URL_RT_OWNED_1", "http://127.0.0.1:9001/")
    assert WorkerInferenceClient.worker_url("rt-owned-1") == "http://127.0.0.1:9001"


def test_worker_url_uses_default_env(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.setenv("AILOVANTA_DEFAULT_WORKER_URL", "http://127.0.0.1:9002")
    assert WorkerInferenceClient.worker_url("rt-owned-1") == "http://127.0.0.1:9002"


def test_worker_url_needs_config(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.delenv("AILOVANTA_DEFAULT_WORKER_URL", raising=False)
    try:
        WorkerInferenceClient.worker_url("rt-owned-1")
    except WorkerInferenceUnavailable as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("configuration required")
