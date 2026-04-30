import sqlite3
from typing import Any

import uuid
from flask import Flask, current_app, g


def get_db() -> sqlite3.Connection:
    keepalive = current_app.extensions.get("db_keepalive")
    if keepalive is not None:
        g.db = keepalive
        return keepalive

    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        uri = isinstance(db_path, str) and db_path.startswith("file:")
        conn = sqlite3.connect(db_path, uri=uri)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(_: Any = None) -> None:
    # Keepalive DB stays open for app lifetime (used for in-memory tests).
    if current_app.extensions.get("db_keepalive") is not None:
        g.pop("db", None)
        return

    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  membership_status TEXT NOT NULL DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS workouts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  workout_type TEXT NOT NULL,
  duration_min INTEGER NOT NULL,
  notes TEXT,
  FOREIGN KEY (client_id) REFERENCES clients(id)
);
"""


def init_db(app: Flask) -> None:
    # Special-case SQLite in-memory for tests:
    # - ":memory:" normally creates a new DB per connection.
    # - Flask opens/closes a connection per request, so data would vanish.
    # Solution: keep one shared-cache in-memory connection alive for the app.
    if app.config.get("DATABASE_PATH") == ":memory:":
        mem_name = f"aceest_fitness_{uuid.uuid4().hex}"
        conn = sqlite3.connect(
            f"file:{mem_name}?mode=memory&cache=shared",
            uri=True,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        app.extensions["db_keepalive"] = conn
        return

    # Non-memory DBs: ensure schema exists once at startup.
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA_SQL)
        db.commit()

