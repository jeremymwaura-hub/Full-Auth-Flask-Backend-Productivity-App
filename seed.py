"""Populate the database with demo users and workouts.

Usage:
    python seed.py

The script is safe to re-run: it drops and recreates all tables, then
inserts demo users (including "demo" / "password") plus a generous number
of randomly generated workouts per user so the paginated index endpoint
has real data to page through.
"""

import re
from random import choice, randint, seed as set_random_seed

from faker import Faker

from app import create_app
from extensions import db
from models import User, Workout

fake = Faker()
Faker.seed(2024)  # Deterministic fake data across runs.
set_random_seed(2024)

ACTIVITIES = [
    "Running", "Cycling", "Swimming", "Weight Training", "Yoga",
    "Walking", "HIIT", "Rowing", "Boxing", "Dancing", "Hiking", "Pilates",
]
INTENSITIES = ["low", "moderate", "high"]

DEMO_USERS = [
    {"username": "demo", "password": "password"},
    {"username": "jane_doe", "password": "password"},
    {"username": "john_doe", "password": "password"},
]


def safe_username():
    """Return a Faker username that satisfies the API's username rules."""
    while True:
        name = re.sub(r"[^\w]", "", fake.user_name()).lower()
        if 3 <= len(name) <= 80:
            return name


def build_workout(user_id):
    """Build a random Workout for the given user."""
    return Workout(
        user_id=user_id,
        activity=choice(ACTIVITIES),
        duration_minutes=randint(15, 120),
        calories_burned=randint(50, 900),
        intensity=choice(INTENSITIES),
        workout_date=fake.date_between(start_date="-365d", end_date="today"),
    )


def seed():
    app = create_app()
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()

        # Demo users + a few Faker users.
        users = []
        for spec in DEMO_USERS:
            user = User(username=spec["username"])
            user.set_password(spec["password"])
            db.session.add(user)
            users.append(user)

        for _ in range(3):
            user = User(username=safe_username())
            user.set_password("password")
            db.session.add(user)
            users.append(user)

        db.session.flush()  # Assign ids so we can reference user.id.

        workout_count = 0
        for user in users:
            for _ in range(randint(12, 30)):
                db.session.add(build_workout(user.id))
                workout_count += 1

        db.session.commit()

        print(f"\nCreated {len(users)} users and {workout_count} workouts.\n")
        print("Demo logins:")
        for user in users:
            password = next(
                (spec["password"] for spec in DEMO_USERS if spec["username"] == user.username),
                "password",
            )
            print(f"  username: {user.username:<16} password: {password}")


if __name__ == "__main__":
    seed()
