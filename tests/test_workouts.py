"""Tests for the workout resource: CRUD, pagination, and ownership rules."""

PASSWORD = "password123"
VALID_PAYLOAD = {
    "activity": "Running",
    "duration_minutes": 30,
    "calories_burned": 250,
    "intensity": "moderate",
    "workout_date": "2024-01-15",
}


def register(client, username="alice"):
    return client.post(
        "/signup",
        json={
            "username": username,
            "password": PASSWORD,
            "password_confirmation": PASSWORD,
        },
    )


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_workout(client, token, **overrides):
    payload = dict(VALID_PAYLOAD)
    payload.update(overrides)
    return client.post("/workouts", json=payload, headers=auth_headers(token))


# ---------------------------------------------------------------- auth gating

def test_workout_routes_require_auth(client):
    assert client.get("/workouts").status_code == 401
    assert client.post("/workouts", json={}).status_code == 401
    assert client.get("/workouts/1").status_code == 401
    assert client.patch("/workouts/1", json={}).status_code == 401
    assert client.delete("/workouts/1").status_code == 401


# ---------------------------------------------------------------- create

def test_create_workout(client):
    token = register(client).get_json()["token"]
    response = create_workout(client, token)

    assert response.status_code == 201
    body = response.get_json()
    assert body["activity"] == "Running"
    assert body["duration_minutes"] == 30
    assert body["calories_burned"] == 250
    assert body["intensity"] == "moderate"
    assert body["workout_date"] == "2024-01-15"
    assert body["user_id"] == 1  # tied to the authenticated user


def test_create_workout_applies_defaults(client):
    token = register(client).get_json()["token"]
    response = client.post(
        "/workouts",
        json={"activity": "Yoga", "duration_minutes": 45},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["calories_burned"] == 0
    assert body["intensity"] == "moderate"


def test_create_workout_validates_payload(client):
    token = register(client).get_json()["token"]
    response = create_workout(client, token, duration_minutes=-5)
    assert response.status_code == 422
    assert response.get_json()["errors"]


def test_create_workout_requires_activity(client):
    token = register(client).get_json()["token"]
    response = client.post(
        "/workouts",
        json={"duration_minutes": 30},
        headers=auth_headers(token),
    )
    assert response.status_code == 422
    assert response.get_json()["errors"]


# ---------------------------------------------------------------- list + pagination

def test_list_workouts_paginated(client):
    token = register(client).get_json()["token"]
    for i in range(25):
        create_workout(client, token, activity=f"Exercise {i}")

    response = client.get("/workouts?page=2&per_page=10", headers=auth_headers(token))
    assert response.status_code == 200

    body = response.get_json()
    assert len(body["workouts"]) == 10
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["per_page"] == 10
    assert body["pagination"]["total"] == 25
    assert body["pagination"]["total_pages"] == 3
    assert body["pagination"]["has_prev"] is True
    assert body["pagination"]["has_next"] is True  # page 3 exists


def test_list_workouts_defaults_to_first_page(client):
    token = register(client).get_json()["token"]
    for _ in range(12):
        create_workout(client, token)

    body = client.get("/workouts", headers=auth_headers(token)).get_json()
    assert len(body["workouts"]) == 10
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["per_page"] == 10


def test_list_workouts_rejects_invalid_pagination(client):
    token = register(client).get_json()["token"]
    headers = auth_headers(token)

    assert client.get("/workouts?page=0", headers=headers).status_code == 422
    assert client.get("/workouts?per_page=0", headers=headers).status_code == 422
    assert client.get("/workouts?page=abc", headers=headers).status_code == 422


# ---------------------------------------------------------------- ownership

def test_user_only_sees_own_workouts(client):
    alice_token = register(client, username="alice").get_json()["token"]
    bob_token = register(client, username="bob").get_json()["token"]

    for _ in range(3):
        create_workout(client, alice_token)
    for _ in range(2):
        create_workout(client, bob_token)

    alice_list = client.get("/workouts", headers=auth_headers(alice_token)).get_json()
    bob_list = client.get("/workouts", headers=auth_headers(bob_token)).get_json()

    assert alice_list["pagination"]["total"] == 3
    assert bob_list["pagination"]["total"] == 2


# ---------------------------------------------------------------- show

def test_get_own_workout(client):
    token = register(client).get_json()["token"]
    workout = create_workout(client, token).get_json()

    response = client.get(f"/workouts/{workout['id']}", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.get_json()["id"] == workout["id"]


def test_cannot_get_other_users_workout(client):
    alice_token = register(client, username="alice").get_json()["token"]
    bob_token = register(client, username="bob").get_json()["token"]
    workout = create_workout(client, alice_token).get_json()

    response = client.get(f"/workouts/{workout['id']}", headers=auth_headers(bob_token))
    assert response.status_code == 404


# ---------------------------------------------------------------- update

def test_patch_own_workout(client):
    token = register(client).get_json()["token"]
    workout = create_workout(client, token).get_json()

    response = client.patch(
        f"/workouts/{workout['id']}",
        json={"duration_minutes": 60, "intensity": "high"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["duration_minutes"] == 60
    assert body["intensity"] == "high"
    assert body["activity"] == "Running"  # untouched fields are preserved


def test_cannot_patch_other_users_workout(client):
    alice_token = register(client, username="alice").get_json()["token"]
    bob_token = register(client, username="bob").get_json()["token"]
    workout = create_workout(client, alice_token).get_json()

    response = client.patch(
        f"/workouts/{workout['id']}",
        json={"duration_minutes": 99},
        headers=auth_headers(bob_token),
    )
    assert response.status_code == 404

    # Alice's record is untouched.
    body = client.get(
        f"/workouts/{workout['id']}", headers=auth_headers(alice_token)
    ).get_json()
    assert body["duration_minutes"] == 30


def test_patch_workout_validates_payload(client):
    token = register(client).get_json()["token"]
    workout = create_workout(client, token).get_json()

    response = client.patch(
        f"/workouts/{workout['id']}",
        json={"intensity": "extreme"},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


# ---------------------------------------------------------------- delete

def test_delete_own_workout(client):
    token = register(client).get_json()["token"]
    workout = create_workout(client, token).get_json()

    response = client.delete(f"/workouts/{workout['id']}", headers=auth_headers(token))
    assert response.status_code == 204

    assert (
        client.get(f"/workouts/{workout['id']}", headers=auth_headers(token)).status_code
        == 404
    )


def test_cannot_delete_other_users_workout(client):
    alice_token = register(client, username="alice").get_json()["token"]
    bob_token = register(client, username="bob").get_json()["token"]
    workout = create_workout(client, alice_token).get_json()

    response = client.delete(f"/workouts/{workout['id']}", headers=auth_headers(bob_token))
    assert response.status_code == 404

    assert (
        client.get(f"/workouts/{workout['id']}", headers=auth_headers(alice_token)).status_code
        == 200
    )
