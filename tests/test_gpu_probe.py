from fastapi.testclient import TestClient

from api.gpu_probe import detect_gpu
from api.main import app


def test_gpu_probe_shape() -> None:
    status = detect_gpu()

    assert "has_gpu" in status
    assert "gpu_name" in status
    assert "gpu_memory_gb" in status
    assert "available_gpu_memory_gb" in status
    assert "cuda_available" in status
    assert "probe_source" in status


def test_local_gpu_endpoint() -> None:
    response = TestClient(app).get("/local/gpu")
    body = response.json()

    assert response.status_code == 200
    assert "has_gpu" in body
    assert "probe_source" in body
