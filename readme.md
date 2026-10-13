# Workout Tracking API

A Flask backend for creating, viewing, and deleting workouts and
exercises. Exercises are reusable across workouts. Workout entries
store sets, reps, and duration.

## Requirements

- Python 3.12
- Pipenv

## Installation

```bash
git clone https://github.com/Macrinejangu/Flask-SQLAlchemy.git
cd Flask-SQLAlchemy
pipenv install --dev
pipenv shell
cd server
flask --app app db upgrade
python seed.py
```

Migrations are included. Seeding replaces existing lab data with
3 exercises, 2 workouts, and 4 workout entries.

## Run

From the server directory:

```bash
flask --app app run --port 5555
```

The API runs at http://localhost:5555.

The default database is SQLite. Set DATABASE_URL to override its location.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | / | Welcome message |
| GET | /workouts | List workouts |
| GET | /workouts/<id> | Workout with exercises and measurements |
| POST | /workouts | Create a workout |
| DELETE | /workouts/<id> | Delete workout and its join records |
| GET | /exercises | List exercises |
| GET | /exercises/<id> | Exercise with associated workouts |
| POST | /exercises | Create an exercise |
| DELETE | /exercises/<id> | Delete exercise and its join records |
| POST | /workouts/<workout_id>/exercises/<exercise_id>/workout_exercises | Add an exercise to a workout |

## Request Examples

Create a workout:

```json
{
  "date": "2026-10-13",
  "duration_minutes": 30,
  "notes": "Strength session"
}
```

Create an exercise:

```json
{
  "name": "Squats",
  "category": "Strength",
  "equipment_needed": false
}
```

Add a strength exercise to a workout:

```json
{
  "reps": 12,
  "sets": 3
}
```

For a timed exercise:

```json
{
  "duration_seconds": 60
}
```

Send request bodies with Content-Type: application/json.

## Validation

Database constraints reject blank exercise names and categories,
non-positive workout durations, and non-positive exercise measurements.
Foreign keys enforce valid parent references.

Model validators check text, dates, booleans, and positive integers.

Marshmallow validates required fields, dates, text lengths, and
positive measurements. Reps and sets must appear together.
Each workout entry requires reps with sets, or duration_seconds.

Deleting a workout or exercise removes its join records and preserves
the other parent records.

## Responses

- 200: Successful retrieval
- 201: Resource created
- 204: Resource deleted, with no response body
- 400: Invalid input or database constraint violation
- 404: Resource not found

## Tests

From the project root:

```bash
pipenv run python -m pytest tests/test_api.py -q
```

Tests use a separate temporary database and cover creation, retrieval,
nested serialization, invalid input, missing resources, cascading
deletes, model validation, and database constraints.