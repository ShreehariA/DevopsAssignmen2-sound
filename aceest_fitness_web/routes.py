from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from .db import get_db

api = Blueprint("api", __name__)


@api.get("/health")
def health():
    return jsonify(status="ok", version=current_app.config["APP_VERSION"])


@api.post("/clients")
def create_client():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify(error="name is required"), 400

    membership_status = (payload.get("membership_status") or "Active").strip() or "Active"
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO clients (name, membership_status) VALUES (?, ?)",
            (name, membership_status),
        )
        db.commit()
    except Exception:
        return jsonify(error="client already exists"), 409

    return jsonify(id=cur.lastrowid, name=name, membership_status=membership_status), 201


@api.get("/clients")
def list_clients():
    db = get_db()
    rows = db.execute(
        "SELECT id, name, membership_status FROM clients ORDER BY id ASC"
    ).fetchall()
    return jsonify(
        clients=[
            {"id": r["id"], "name": r["name"], "membership_status": r["membership_status"]}
            for r in rows
        ]
    )


@api.post("/clients/<int:client_id>/workouts")
def add_workout(client_id: int):
    payload = request.get_json(silent=True) or {}
    date = (payload.get("date") or "").strip()
    workout_type = (payload.get("workout_type") or "").strip()
    duration_min = payload.get("duration_min")
    notes = payload.get("notes")

    if not date or not workout_type or duration_min is None:
        return jsonify(error="date, workout_type, duration_min are required"), 400

    db = get_db()
    client = db.execute("SELECT id FROM clients WHERE id=?", (client_id,)).fetchone()
    if client is None:
        return jsonify(error="client not found"), 404

    cur = db.execute(
        """
        INSERT INTO workouts (client_id, date, workout_type, duration_min, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (client_id, date, workout_type, int(duration_min), notes),
    )
    db.commit()
    return jsonify(id=cur.lastrowid), 201


@api.get("/clients/<int:client_id>/workouts")
def list_workouts(client_id: int):
    db = get_db()
    rows = db.execute(
        """
        SELECT id, date, workout_type, duration_min, notes
        FROM workouts
        WHERE client_id=?
        ORDER BY date DESC, id DESC
        """,
        (client_id,),
    ).fetchall()

    return jsonify(
        workouts=[
            {
                "id": r["id"],
                "date": r["date"],
                "workout_type": r["workout_type"],
                "duration_min": r["duration_min"],
                "notes": r["notes"],
            }
            for r in rows
        ]
    )

