"""Workout resources: list (paginated), create, show, update, delete.

Ownership rule
--------------
Every workout belongs to exactly one user (Workout.user_id). Each query
here filters by BOTH the requested workout id and the authenticated user's
id, so one user can never read, update, or delete another user's records.
Requests for another user's workout return 404 (we deliberately do not
reveal whether a workout exists).
"""

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from marshmallow import ValidationError

from extensions import db
from models import Workout
from schemas import PaginationSchema, WorkoutSchema, WorkoutUpdateSchema
from utils import flatten_marshmallow_errors


def _current_user_id():
    """Parse the authenticated user's id out of the JWT identity."""
    return int(get_jwt_identity())


class WorkoutListResource(Resource):
    """GET /workouts (paginated) and POST /workouts."""

    @jwt_required()
    def get(self):
        user_id = _current_user_id()

        try:
            query_params = PaginationSchema().load(request.args.to_dict())
        except ValidationError as err:
            return {"errors": flatten_marshmallow_errors(err)}, 422

        page = query_params["page"]
        per_page = query_params["per_page"]

        workouts = (
            Workout.query.filter_by(user_id=user_id)
            .order_by(Workout.workout_date.desc(), Workout.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return {
            "workouts": WorkoutSchema().dump(workouts.items, many=True),
            "pagination": {
                "page": workouts.page,
                "per_page": workouts.per_page,
                "total": workouts.total,
                "total_pages": workouts.pages,
                "has_prev": workouts.has_prev,
                "has_next": workouts.has_next,
            },
        }, 200

    @jwt_required()
    def post(self):
        user_id = _current_user_id()
        payload = request.get_json(silent=True) or {}

        try:
            data = WorkoutSchema().load(payload)
        except ValidationError as err:
            return {"errors": flatten_marshmallow_errors(err)}, 422

        workout = Workout(user_id=user_id, **data)
        db.session.add(workout)
        db.session.commit()

        return WorkoutSchema().dump(workout), 201


class WorkoutDetailResource(Resource):
    """GET /workouts/<id>, PATCH /workouts/<id>, DELETE /workouts/<id>."""

    @staticmethod
    def _get_owned_workout(workout_id):
        """Return the workout only if it belongs to the current user."""
        user_id = _current_user_id()
        return Workout.query.filter_by(id=workout_id, user_id=user_id).first()

    @jwt_required()
    def get(self, workout_id):
        workout = self._get_owned_workout(workout_id)
        if workout is None:
            return {"errors": ["Workout not found."]}, 404
        return WorkoutSchema().dump(workout), 200

    @jwt_required()
    def patch(self, workout_id):
        workout = self._get_owned_workout(workout_id)
        if workout is None:
            return {"errors": ["Workout not found."]}, 404

        payload = request.get_json(silent=True) or {}
        try:
            data = WorkoutUpdateSchema().load(payload)
        except ValidationError as err:
            return {"errors": flatten_marshmallow_errors(err)}, 422

        for field, value in data.items():
            setattr(workout, field, value)
        db.session.commit()

        return WorkoutSchema().dump(workout), 200

    @jwt_required()
    def delete(self, workout_id):
        workout = self._get_owned_workout(workout_id)
        if workout is None:
            return {"errors": ["Workout not found."]}, 404

        db.session.delete(workout)
        db.session.commit()

        return "", 204
