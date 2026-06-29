import httpx

from api.runtime_forwarder import RuntimeEndpointStore
from api.worker_transport import WorkerInferenceClient, WorkerInferenceRequest, WorkerInferenceUnavailable


def test_worker_url_uses_specific_env(monkeypatch) -> None:
    monkeypatch.setenv("AILOVANTA_WORKER_URL_RT_OWNED_1", "http://127.0.0.1:9001/")
    assert WorkerInferenceClient.worker_url("rt-owned-1") == "http://127.0.0.1:9001"


def test_worker_url_uses_default_env(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.setenv("AILOVANTA_DEFAULT_WORKER_URL", "http://127.0.0.1:9002")
    assert WorkerInferenceClient.worker_url("rt-owned-1") == "http://127.0.0.1:9002"


def test_worker_url_uses_endpoint_registry(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.delenv("AILOVANTA_DEFAULT_WORKER_URL", raising=False)
    store = RuntimeEndpointStore(tmp_path / "runtime_endpoints.json")
    store.register("rt-owned-1", "http://worker.local/")
    assert WorkerInferenceClient.worker_url("rt-owned-1", store) == "http://worker.local"


def test_worker_infer_posts_to_registered_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.delenv("AILOVANTA_DEFAULT_WORKER_URL", raising=False)
    store = RuntimeEndpointStore(tmp_path / "runtime_endpoints.json")
    store.register("rt-owned-1", "http://worker.local")

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://worker.local/v1/owned/infer"
        body = request.read().decode("utf-8")
        assert "hello" in body
        return httpx.Response(200, json={"answer": "worker answer", "source": "test-worker"})

    client = WorkerInferenceClient(endpoint_store=store, transport=httpx.MockTransport(handler))
    result = client.infer(
        WorkerInferenceRequest(
            prompt="hello",
            model_id="ailovanta-owned",
            version="candidate",
            policy_mode="open_research",
            runtime_id="rt-owned-1",
            node_id="node-owned-1",
            model_manifest_hash="sha256:model",
        )
    )
    assert result.answer == "worker answer"
    assert result.worker_url == "http://worker.local"


def test_worker_url_needs_config(monkeypatch) -> None:
    monkeypatch.delenv("AILOVANTA_WORKER_URL_RT_OWNED_1", raising=False)
    monkeypatch.delenv("AILOVANTA_DEFAULT_WORKER_URL", raising=False)
    try:
        WorkerInferenceClient.worker_url("rt-owned-1")
    except WorkerInferenceUnavailable as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("configuration required")
