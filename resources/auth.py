"""Authentication resources: signup, login, and current-user ("me").

Contract (matches the provided JWT React client):
  POST /signup  -> {token, user}      on success (201)
  POST /login   -> {token, user}      on success (200)
  GET  /me      -> {id, username}     with a valid Bearer token (200)

All error responses use the shape {"errors": [message, ...]} so the client
can display them directly.
"""

from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User
from schemas import LoginSchema, SignupSchema, user_schema
from utils import flatten_marshmallow_errors


class SignupResource(Resource):
    """POST /signup — register a new user and return a JWT."""

    def post(self):
        payload = request.get_json(silent=True) or {}

        try:
            data = SignupSchema().load(payload)
        except ValidationError as err:
            return {"errors": flatten_marshmallow_errors(err)}, 422

        if User.query.filter_by(username=data["username"]).first():
            return {"errors": ["Username is already taken."]}, 409

        user = User(username=data["username"])
        user.set_password(data["password"])

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:  # Race-condition fallback for duplicate username
            db.session.rollback()
            return {"errors": ["Username is already taken."]}, 409

        token = create_access_token(identity=str(user.id))
        return {"token": token, "user": user_schema.dump(user)}, 201


class LoginResource(Resource):
    """POST /login — authenticate an existing user and return a JWT."""

    def post(self):
        payload = request.get_json(silent=True) or {}

        try:
            data = LoginSchema().load(payload)
        except ValidationError as err:
            return {"errors": flatten_marshmallow_errors(err)}, 422

        user = User.query.filter_by(username=data["username"]).first()
        if user is None or not user.check_password(data["password"]):
            # One generic message for both cases so the response never
            # reveals whether a username exists.
            return {"errors": ["Invalid username or password."]}, 401

        token = create_access_token(identity=str(user.id))
        return {"token": token, "user": user_schema.dump(user)}, 200


class MeResource(Resource):
    """GET /me — return the currently authenticated user."""

    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if user is None:
            return {"errors": ["User not found."]}, 404
        return user_schema.dump(user), 200
