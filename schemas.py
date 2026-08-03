"""Marshmallow schemas.

Each schema does double duty:
  * validates incoming JSON (request payloads), and
  * serializes model instances to JSON (responses).

The API never serializes `password_hash` — see UserSchema.
"""

from datetime import date

from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema

USERNAME_VALIDATOR = validate.And(
    validate.Length(min=3, max=80, error="Username must be between 3 and 80 characters."),
    validate.Regexp(
        r"^\w+$",
        error="Username may only contain letters, numbers, and underscores.",
    ),
)

PASSWORD_VALIDATOR = validate.Length(min=8, error="Password must be at least 8 characters.")


class SignupSchema(Schema):
    """Request validation for POST /signup."""

    username = fields.Str(required=True, validate=USERNAME_VALIDATOR)
    password = fields.Str(required=True, validate=PASSWORD_VALIDATOR)
    password_confirmation = fields.Str(required=True)

    @validates_schema
    def validate_confirmation(self, data, **kwargs):
        if data.get("password") != data.get("password_confirmation"):
            raise ValidationError(
                "Passwords do not match.", field_name="password_confirmation"
            )


class LoginSchema(Schema):
    """Request validation for POST /login."""

    username = fields.Str(required=True)
    password = fields.Str(required=True)


class UserSchema(Schema):
    """Serialization of a user. Password data is never exposed."""

    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class WorkoutSchema(Schema):
    """Validation for POST /workouts and serialization of a workout."""

    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)

    activity = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100, error="Activity is required (max 100 characters)."),
    )
    duration_minutes = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=1440, error="Duration must be between 1 and 1440 minutes."),
    )
    calories_burned = fields.Int(
        load_default=0,
        validate=validate.Range(min=0, error="Calories burned cannot be negative."),
    )
    intensity = fields.Str(
        load_default="moderate",
        validate=validate.OneOf(["low", "moderate", "high"], error="Intensity must be low, moderate, or high."),
    )
    workout_date = fields.Date(load_default=lambda: date.today())

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class WorkoutUpdateSchema(Schema):
    """Validation for PATCH /workouts/<id> — every field is optional."""

    activity = fields.Str(
        validate=validate.Length(min=1, max=100, error="Activity must be between 1 and 100 characters.")
    )
    duration_minutes = fields.Int(
        validate=validate.Range(min=1, max=1440, error="Duration must be between 1 and 1440 minutes.")
    )
    calories_burned = fields.Int(validate=validate.Range(min=0, error="Calories burned cannot be negative."))
    intensity = fields.Str(
        validate=validate.OneOf(["low", "moderate", "high"], error="Intensity must be low, moderate, or high.")
    )
    workout_date = fields.Date()


class PaginationSchema(Schema):
    """Validation for the ?page= and ?per_page= query parameters."""

    page = fields.Int(load_default=1, validate=validate.Range(min=1, error="Page must be at least 1."))
    per_page = fields.Int(
        load_default=10,
        validate=validate.Range(min=1, max=100, error="Per page must be between 1 and 100."),
    )

    class Meta:
        # Ignore any other query params a client may send.
        unknown = EXCLUDE


# Reusable schema instances.
user_schema = UserSchema()
