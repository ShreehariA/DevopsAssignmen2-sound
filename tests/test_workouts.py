from aceest_fitness_web import create_app


def test_add_and_list_workouts(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    app = create_app()
    c = app.test_client()

    new_client = c.post("/clients", json={"name": "Charlie"})
    client_id = new_client.get_json()["id"]

    r1 = c.post(
        f"/clients/{client_id}/workouts",
        json={
            "date": "2026-04-27",
            "workout_type": "Strength",
            "duration_min": 45,
            "notes": "Squats and bench",
        },
    )
    assert r1.status_code == 201

    r2 = c.get(f"/clients/{client_id}/workouts")
    assert r2.status_code == 200
    workouts = r2.get_json()["workouts"]
    assert len(workouts) == 1
    assert workouts[0]["workout_type"] == "Strength"


def test_add_workout_requires_fields(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    app = create_app()
    c = app.test_client()

    new_client = c.post("/clients", json={"name": "Dana"})
    client_id = new_client.get_json()["id"]

    r = c.post(f"/clients/{client_id}/workouts", json={"date": "2026-04-27"})
    assert r.status_code == 400


def test_add_workout_unknown_client(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    app = create_app()
    c = app.test_client()

    r = c.post(
        "/clients/999/workouts",
        json={"date": "2026-04-27", "workout_type": "Cardio", "duration_min": 30},
    )
    assert r.status_code == 404

