"""Pytest fixtures: a fresh app + test client per test."""

import pytest

from app import create_app
from config import TestingConfig
from extensions import db


@pytest.fixture()
def app(tmp_path):
    """Create the app with a temp-file SQLite database, tables ready."""
    application = create_app(TestingConfig)
    # Use a real temp file (not :memory:) to avoid SQLite connection-pool quirks.
    application.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"

    with application.app_context():
        db.create_all()

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """A Flask test client bound to the fixture app."""
    return app.test_client()
