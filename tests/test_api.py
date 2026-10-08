from app.main import app, probe_database


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body == {"status": "ok", "data_mode": "fixture", "region": "singrauli", "database": "ok"}


def test_health_degraded_without_db(client):
    app.dependency_overrides[probe_database] = lambda: "unavailable"
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degraded"


def test_region_returns_configured_bbox(client):
    r = client.get("/region")
    assert r.status_code == 200
    assert r.json() == {"name": "singrauli", "bbox": [82.30, 23.85, 82.95, 24.45]}
