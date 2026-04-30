from aceest_fitness_web import create_app


def test_health_returns_ok_and_version(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "3.2.4")
    monkeypatch.setenv("DATABASE_PATH", ":memory:")

    app = create_app()
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["version"] == "3.2.4"

