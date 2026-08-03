# 🏋️ Workout Tracker API — Full Auth Flask Backend

A secure, RESTful **Flask API** for a productivity app. It implements complete
**JWT-based authentication** (signup, login, session persistence) and a
**user-owned resource — workout logs** — with full CRUD, ownership protection,
and pagination.

This is the backend half of the *Summative Lab: Full Auth Flask Backend –
Productivity Tool*. The frontend team's React client (`client-with-jwt`) is
provided separately and connects to this API as-is.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup (Migrations)](#database-setup-migrations)
  - [Seeding the Database](#seeding-the-database)
  - [Running the Server](#running-the-server)
- [Testing](#testing)
- [API Reference](#api-reference)
  - [Authentication Endpoints](#authentication-endpoints)
  - [Workout Endpoints](#workout-endpoints)
- [Authentication & Authorization](#authentication--authorization)
- [Pagination](#pagination)
- [Error Format](#error-format)
- [Security Notes](#security-notes)
- [Frontend Integration](#frontend-integration)

---

## Features

- ✅ Full authentication: **signup**, **login**, and **current user (`/me`)** endpoints using **JWT** (`flask-jwt-extended`)
- ✅ Passwords hashed with **Flask-Bcrypt** — plain-text passwords are never stored
- ✅ A **user-owned resource** (workouts) with complete **CRUD**:
  - `GET /workouts` — paginated list of *your* workouts
  - `POST /workouts` — log a new workout
  - `PATCH /workouts/<id>` — edit a workout
  - `DELETE /workouts/<id>` — delete a workout
- ✅ **Ownership protection** — users can only see/manipulate their own records; every query filters by the authenticated user
- ✅ **Pagination** with `?page=` and `?per_page=` query parameters and pagination metadata in the response
- ✅ Input validation with **Marshmallow** (consistent, readable error messages)
- ✅ Database migrations with **Flask-Migrate** / Alembic
- ✅ Modular, production-shaped project structure (app factory + separate modules)
- ✅ Automated test suite (28 tests) with **pytest**
- ✅ Seed script with demo users and realistic sample data (Faker)

## Tech Stack

| Layer        | Technology                                        |
| ------------ | ------------------------------------------------- |
| Web framework| Flask 2.2.2                                       |
| ORM          | Flask-SQLAlchemy 3.0.3 + SQLAlchemy 2.x           |
| Migrations   | Flask-Migrate 4.0.0 (Alembic)                     |
| Auth         | flask-jwt-extended 4.4.4 (JWT Bearer tokens)      |
| Passwords    | Flask-Bcrypt 1.0.1                                |
| Validation   | Marshmallow 3.20.1                                |
| API          | Flask-RESTful 0.3.9                               |
| Seed data    | Faker 15.3.2                                      |
| Tests        | pytest 7.2.0                                      |
| CORS         | flask-cors                                        |

## Project Structure

```
workout-tracker-api/
├── app.py                    # App factory + entry point (flask run / python app.py)
├── config.py                 # Environment-based configuration classes
├── extensions.py             # Centralised Flask extension instances
├── models.py                 # User & Workout models
├── schemas.py                # Marshmallow schemas (validation + serialization)
├── seed.py                   # Database seed script (demo users + workouts)
├── utils.py                  # Shared helpers (error formatting)
├── resources/
│   ├── __init__.py
│   ├── auth.py               # /signup, /login, /me
│   └── workouts.py           # /workouts, /workouts/<id>
├── migrations/               # Flask-Migrate / Alembic migration scripts
├── tests/                    # pytest suite (28 tests)
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_workouts.py
├── Pipfile / Pipfile.lock    # Dependencies (Pipenv)
├── .flaskenv                 # Flask CLI defaults (port 5555)
├── .env.example              # Template for environment variables
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Python **3.8.13+**
- [Pipenv](https://pipenv.pypa.io/) (`pip install pipenv`)
- Git

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url> workout-tracker-api
cd workout-tracker-api

# 2. Install dependencies from the Pipfile
pipenv install --dev

# 3. Activate the virtual environment
pipenv shell
```

> `--dev` installs dev dependencies too (pytest).

### Environment Variables

The app runs out of the box with safe dev defaults, but for anything beyond
local development you should create a `.env` file:

```bash
cp .env.example .env
```

| Variable        | Required | Description                                        |
| --------------- | -------- | -------------------------------------------------- |
| `SECRET_KEY`    | dev: no  | Flask secret key                                   |
| `JWT_SECRET_KEY`| dev: no  | Key used to sign JWT access tokens                 |
| `DATABASE_URL`  | dev: no  | SQLAlchemy database URL (defaults to local SQLite) |

### Database Setup (Migrations)

```bash
# Create the database and apply all migrations
flask db upgrade
```

If you ever change a model, create a new migration and apply it:

```bash
flask db migrate -m "describe your change"
flask db upgrade
```

### Seeding the Database

```bash
python seed.py
```

This drops and recreates all tables, then creates **6 demo users** and
**100+ workouts**. Demo logins (password for all is `password`):

| Username   | Password |
| ---------- | -------- |
| `demo`     | `password` |
| `jane_doe` | `password` |
| `john_doe` | `password` |
| *(3 more Faker-generated users)* | `password` |

### Running the Server

```bash
# Option A — Flask CLI (uses .flaskenv: port 5555)
flask run

# Option B — run app.py directly
python app.py
```

The API listens on **http://localhost:5555** (both provided frontend clients
proxy API calls to this port).

---

## Testing

```bash
pytest -v
```

The suite covers: signup validation, duplicate usernames, login success/failure,
`/me` authorization, workout CRUD, pagination, input validation, and
cross-user access denial.

---

## API Reference

All requests and responses are JSON.

### Authentication Endpoints

| Method | Endpoint     | Description                                                       | Auth |
| ------ | ------------ | ----------------------------------------------------------------- | ---- |
| POST   | `/signup`    | Register a new user and return a JWT access token                 | —    |
| POST   | `/login`     | Log in an existing user and return a JWT access token             | —    |
| GET    | `/me`        | Return the currently authenticated user (persists login on refresh)| ✅   |

#### `POST /signup` — Register

**Request body:**

```json
{
  "username": "alice",
  "password": "password123",
  "password_confirmation": "password123"
}
```

**Success — `201 Created`:**

```json
{
  "token": "<jwt-access-token>",
  "user": {
    "id": 1,
    "username": "alice",
    "created_at": "2024-06-10T10:30:00.000000"
  }
}
```

**Errors:** `422` (missing/invalid fields, passwords don't match, password < 8 chars) · `409` (username already taken).

#### `POST /login` — Log in

**Request body:** `{ "username": "alice", "password": "password123" }`

**Success — `200 OK`:** same shape as signup (`token` + `user`).

**Errors:** `401` (invalid username or password — one generic message so the API never reveals which one was wrong) · `422` (missing fields).

#### `GET /me` — Current user

**Header:** `Authorization: Bearer <token>`

**Success — `200 OK`:**

```json
{ "id": 1, "username": "alice", "created_at": "2024-06-10T10:30:00.000000" }
```

**Errors:** `401` (missing/expired/invalid token).

### Workout Endpoints

Workouts belong to the authenticated user — the `user_id` on every workout is
taken from the JWT, never from the request body.

| Method | Endpoint            | Description                                             | Auth |
| ------ | ------------------- | ------------------------------------------------------- | ---- |
| GET    | `/workouts`         | Paginated list of the current user's workouts           | ✅   |
| POST   | `/workouts`         | Create a new workout                                    | ✅   |
| GET    | `/workouts/<id>`    | Fetch one of the current user's workouts                | ✅   |
| PATCH  | `/workouts/<id>`    | Update one of the current user's workouts (partial)     | ✅   |
| DELETE | `/workouts/<id>`    | Delete one of the current user's workouts               | ✅   |

Workout fields:

| Field              | Type   | Required | Notes                                        |
| ------------------ | ------ | -------- | -------------------------------------------- |
| `activity`         | string | ✅       | e.g. "Running", "Cycling" (max 100 chars)    |
| `duration_minutes` | int    | ✅       | 1 – 1440                                     |
| `calories_burned`  | int    | —        | default `0`                                  |
| `intensity`        | string | —        | `low` \| `moderate` \| `high` (default `moderate`) |
| `workout_date`     | date   | —        | `YYYY-MM-DD`, defaults to today              |

#### `GET /workouts` — Paginated list

**Query params:** `page` (default `1`), `per_page` (default `10`, max `100`).

**Success — `200 OK`:**

```json
{
  "workouts": [
    {
      "id": 110,
      "user_id": 7,
      "activity": "Cycling",
      "duration_minutes": 60,
      "calories_burned": 320,
      "intensity": "high",
      "workout_date": "2024-06-10",
      "created_at": "2024-06-10T08:00:00.000000",
      "updated_at": "2024-06-10T09:15:00.000000"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "total_pages": 3,
    "has_prev": false,
    "has_next": true
  }
}
```

**Errors:** `401` (not authenticated) · `422` (invalid `page`/`per_page`).

#### `POST /workouts` — Create

**Request body:**

```json
{
  "activity": "Swimming",
  "duration_minutes": 45,
  "calories_burned": 300,
  "intensity": "moderate",
  "workout_date": "2024-06-12"
}
```

**Success — `201 Created`:** the created workout (see shape above).

**Errors:** `401` · `422` (validation failures).

#### `GET /workouts/<id>` — Show

**Success — `200 OK`:** the workout. **Errors:** `401` · `404`.

#### `PATCH /workouts/<id>` — Update (partial)

Any subset of fields may be sent; omitted fields are preserved.

```json
{ "duration_minutes": 75, "intensity": "high" }
```

**Success — `200 OK`:** the updated workout. **Errors:** `401` · `404` · `422`.

#### `DELETE /workouts/<id>` — Delete

**Success — `204 No Content`.** **Errors:** `401` · `404`.

---

## Authentication & Authorization

1. **Registration/Login:** a user supplies `username` + `password`. The password is hashed with bcrypt (via `User.set_password`).
2. **Token:** on success the API returns a signed JWT access token (`flask-jwt-extended`). The token's identity is the user's id.
3. **Protection:** every workout endpoint is decorated with `@jwt_required()`. Unauthenticated requests get `401`.
4. **Ownership:** each query filters by **both** the requested id and the current user's id:
   ```python
   Workout.query.filter_by(id=workout_id, user_id=user_id).first()
   ```
   Requests for another user's workout return **`404 Not Found`** — we deliberately avoid revealing whether a record exists.

## Pagination

The index endpoint supports:

```
GET /workouts?page=2&per_page=20
```

- `page` — 1-based page number (default `1`)
- `per_page` — items per page (default `10`, max `100`)
- Invalid values return `422`

The response wraps the page's items in `workouts` and includes a `pagination`
object with `page`, `per_page`, `total`, `total_pages`, `has_prev`, and
`has_next` so the frontend can render pager controls.

## Error Format

Every error response follows the same shape (which the provided JWT React
client renders directly):

```json
{ "errors": ["field: readable message"] }
```

| Status | Meaning                                                    |
| ------ | ---------------------------------------------------------- |
| 200    | OK                                                         |
| 201    | Created                                                    |
| 204    | Deleted (no body)                                          |
| 401    | Missing/expired/invalid token, or bad credentials          |
| 404    | Resource not found (including other users' records)        |
| 409    | Username already taken                                     |
| 422    | Validation failed (body or query params)                   |
| 500    | Internal server error (rolled back)                        |

## Security Notes

- Passwords are never stored or returned — only a bcrypt hash lives in the database.
- JWT secret key is configurable via environment variable (`JWT_SECRET_KEY`); never commit real secrets.
- Tokens expire after **24 hours** (configurable via `JWT_ACCESS_TOKEN_EXPIRES`).
- Generic login failure message prevents username enumeration.
- Owned-resource queries are scoped by user id, so horizontal privilege escalation is not possible.
- `user_id` can never be set by the client — it always comes from the JWT.

## Frontend Integration

The provided **`client-with-jwt`** React app works with this backend unchanged:

1. Run the backend on port `5555` (default).
2. From the `client-with-jwt` folder: `npm install && npm start`.
3. The React dev server proxies `/signup`, `/login`, and `/me` to
   `http://localhost:5555` (see `package.json` → `proxy`).

The frontend team can now build the workout screens against:

- `GET /workouts?page=1&per_page=10`
- `POST /workouts`, `PATCH /workouts/<id>`, `DELETE /workouts/<id>`

all sending `Authorization: Bearer <token>` headers.
