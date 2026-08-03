"""Application factory and entry point.

Run with:
    flask run          # uses .flaskenv (port 5555)
    python app.py      # equivalent
"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import api, bcrypt, db, jwt, migrate

# create_app() may be called several times in one process (tests, seed,
# flask CLI). Flask-RESTful's Api cannot register the same endpoints twice,
# so resources are registered exactly once, guarded by this flag.
_resources_registered = False


def _register_resources():
    global _resources_registered
    if _resources_registered:
        return

    from resources.auth import LoginResource, MeResource, SignupResource
    from resources.workouts import WorkoutDetailResource, WorkoutListResource

    api.add_resource(SignupResource, "/signup")
    api.add_resource(LoginResource, "/login")
    api.add_resource(MeResource, "/me")
    api.add_resource(WorkoutListResource, "/workouts")
    api.add_resource(WorkoutDetailResource, "/workouts/<int:workout_id>")

    _resources_registered = True


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialise extensions (instances live in extensions.py).
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    # Keep JSON keys in definition order instead of alphabetical.
    app.json.sort_keys = False

    # ---- Routes ----
    _register_resources()
    api.init_app(app)

    _register_error_handlers(app)

    return app


def _register_error_handlers(app):
    """Keep every error response in the {"errors": [...]} JSON shape."""

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"errors": ["Authentication required. Provide a valid token."]}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"errors": [f"Invalid token: {reason}"]}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"errors": ["Token has expired. Please log in again."]}), 401

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"errors": ["The requested resource was not found."]}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return jsonify({"errors": ["An internal server error occurred."]}), 500


# Module-level instance so `flask run` and `flask db ...` can find the app.
app = create_app()

if __name__ == "__main__":
    # Both provided frontend clients proxy API calls to port 5555.
    app.run(port=5555, debug=True)
