"""Database models.

User   — the account used for authentication (unique username, bcrypt hash).
Workout — the user-owned resource: every workout belongs to exactly one user
          via the `user_id` foreign key.
"""

from datetime import date, datetime, timezone

from extensions import bcrypt, db


def utcnow():
    """Timezone-aware 'now' helper used as the default for timestamps."""
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    # Unique + indexed so `username` can be used as a stable identifier.
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # Deleting a user removes all of their workouts.
    workouts = db.relationship(
        "Workout",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        """Hash a plain-text password with Flask-Bcrypt and store the hash."""
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """Return True if `password` matches the stored hash, else False."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username!r}>"


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    activity = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Integer, default=0, nullable=False)
    # One of: low | moderate | high
    intensity = db.Column(db.String(20), default="moderate", nullable=False)
    workout_date = db.Column(db.Date, default=date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="workouts")

    def __repr__(self):
        return f"<Workout {self.activity!r} ({self.duration_minutes} min)>"
