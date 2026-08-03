"""Application configuration.

Environment variables are read here so the same codebase can run in
development, testing, and (eventually) production without code changes.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by every environment."""

    # Used for Flask's session signing; keep it secret in production.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production")

    # ---- JWT (flask-jwt-extended) ----
    # Separate key so the JWT signing secret can be rotated independently.
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    # Access tokens are valid for 24 hours.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # ---- Database ----
    # SQLite by default; override with DATABASE_URL in other environments.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app.db"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Overridden per test run in tests/conftest.py with a temp-file SQLite DB.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    # Production must provide real secrets; do not fall back to defaults.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
