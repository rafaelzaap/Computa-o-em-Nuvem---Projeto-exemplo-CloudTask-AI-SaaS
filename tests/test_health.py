from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["version"] == "0.3.0"
    assert response.json()["docs"] == "/docs"


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "db": "ok"}


def test_openapi_contains_main_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/tasks" in paths
    assert "/uploads" in paths
