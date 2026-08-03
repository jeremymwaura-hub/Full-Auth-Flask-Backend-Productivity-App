"""Centralised Flask extension instances.

Each extension is created once here and initialised inside the app factory
in app.py. Keeping them in their own module avoids the circular imports
that occur when models/resources import `db` directly from `app`.
"""

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
api = Api()
