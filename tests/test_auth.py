"""Tests for the authentication endpoints and the User model."""

import pytest
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User

PASSWORD = "password123"


def register(client, username="alice", password=PASSWORD, confirmation=None):
    return client.post(
        "/signup",
        json={
            "username": username,
            "password": password,
            "password_confirmation": confirmation if confirmation is not None else password,
        },
    )


def login(client, username="alice", password=PASSWORD):
    return client.post("/login", json={"username": username, "password": password})


# ---------------------------------------------------------------- signup

def test_signup_creates_user_and_returns_token(client, app):
    response = register(client)
    assert response.status_code == 201

    body = response.get_json()
    assert body["token"]
    assert body["user"]["id"] == 1
    assert body["user"]["username"] == "alice"
    assert "password" not in body["user"]  # hash must never be serialized

    with app.app_context():
        user = db.session.get(User, 1)
        assert user is not None
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_signup_rejects_duplicate_username(client):
    assert register(client).status_code == 201
    response = register(client)
    assert response.status_code == 409
    assert isinstance(response.get_json()["errors"], list)


def test_signup_rejects_password_mismatch(client):
    response = register(client, confirmation="a-different-password")
    assert response.status_code == 422
    assert any("match" in error for error in response.get_json()["errors"])


def test_signup_rejects_short_password(client):
    response = register(client, password="short")
    assert response.status_code == 422
    assert response.get_json()["errors"]


def test_signup_rejects_missing_fields(client):
    response = client.post("/signup", json={})
    assert response.status_code == 422
    assert response.get_json()["errors"]


# ---------------------------------------------------------------- login

def test_login_returns_token(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    body = response.get_json()
    assert body["token"]
    assert body["user"]["username"] == "alice"


def test_login_rejects_wrong_password(client):
    register(client)
    response = login(client, password="wrong-password")
    assert response.status_code == 401
    assert response.get_json()["errors"]


def test_login_rejects_unknown_user(client):
    response = login(client, username="nobody")
    assert response.status_code == 401


# ---------------------------------------------------------------- /me

def test_me_returns_current_user(client):
    token = register(client).get_json()["token"]
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"


def test_me_requires_token(client):
    assert client.get("/me").status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


# ---------------------------------------------------------------- model

def test_username_uniqueness_enforced_in_database(app):
    with app.app_context():
        user_one = User(username="unique_user")
        user_one.set_password(PASSWORD)
        user_two = User(username="unique_user")
        user_two.set_password(PASSWORD)

        db.session.add_all([user_one, user_two])
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
