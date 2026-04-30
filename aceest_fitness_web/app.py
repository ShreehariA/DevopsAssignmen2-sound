import os

from flask import Flask

from .db import close_db, init_db
from .routes import api


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.from_mapping(
        APP_VERSION=os.getenv("APP_VERSION", "0.1.0"),
        DATABASE_PATH=os.getenv("DATABASE_PATH", "/tmp/aceest_fitness.db"),
        JSON_SORT_KEYS=False,
    )

    init_db(app)
    app.register_blueprint(api)
    app.teardown_appcontext(close_db)

    return app

