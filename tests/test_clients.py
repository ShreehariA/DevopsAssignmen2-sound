from aceest_fitness_web import create_app


def make_client():
    app = create_app()
    return app.test_client()


def test_create_and_list_clients(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    c = make_client()

    r1 = c.post("/clients", json={"name": "Alice", "membership_status": "Active"})
    assert r1.status_code == 201
    body = r1.get_json()
    assert body["name"] == "Alice"

    r2 = c.get("/clients")
    assert r2.status_code == 200
    data = r2.get_json()
    assert any(x["name"] == "Alice" for x in data["clients"])


def test_create_client_requires_name(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    c = make_client()

    r = c.post("/clients", json={})
    assert r.status_code == 400


def test_duplicate_client_returns_409(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    c = make_client()

    assert c.post("/clients", json={"name": "Bob"}).status_code == 201
    assert c.post("/clients", json={"name": "Bob"}).status_code == 409

