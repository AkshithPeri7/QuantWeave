from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "QuantWeave API"
    assert data["health"] == "/health"
    assert data["docs"] == "/docs"


def test_health_endpoint_healthy(client: TestClient, monkeypatch):
    # Mock check_db_health to return healthy
    import app.api.routes.health as health_module
    monkeypatch.setattr(health_module, "check_db_health", lambda: (True, "connected"))

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "quantweave-api"
    assert data["database"] == "connected"
    assert data["demo_mode"] is True


def test_health_endpoint_degraded(client: TestClient, monkeypatch):
    # Mock check_db_health to simulate database failure
    import app.api.routes.health as health_module
    monkeypatch.setattr(health_module, "check_db_health", lambda: (False, "Connection refused"))

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert "unavailable" in data["database"]
