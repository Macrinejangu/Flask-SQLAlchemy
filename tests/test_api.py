import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy.exc import IntegrityError

test_directory = TemporaryDirectory()
database_path = Path(test_directory.name) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{database_path}"

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from app import app
from models import db, Exercise, Workout, WorkoutExercise


@pytest.fixture()
def client():
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

    yield app.test_client()

    with app.app_context():
        db.session.remove()
        db.drop_all()


def create_pair(client):
    workout_response = client.post("/workouts", json={
        "date": "2026-10-13",
        "duration_minutes": 30,
        "notes": "Test workout",
    })
    exercise_response = client.post("/exercises", json={
        "name": "Squats",
        "category": "Strength",
        "equipment_needed": False,
    })

    assert workout_response.status_code == 201
    assert exercise_response.status_code == 201

    return (
        workout_response.get_json()["id"],
        exercise_response.get_json()["id"],
    )


def test_create_list_and_detail(client):
    workout_id, exercise_id = create_pair(client)

    assert len(client.get("/workouts").get_json()) == 1
    assert len(client.get("/exercises").get_json()) == 1
    assert client.get(f"/workouts/{workout_id}").status_code == 200
    assert client.get(f"/exercises/{exercise_id}").status_code == 200


def test_relationship_serialization(client):
    workout_id, exercise_id = create_pair(client)
    response = client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises",
        json={"reps": 12, "sets": 3},
    )

    assert response.status_code == 201
    assert response.get_json()["reps"] == 12

    workout = client.get(f"/workouts/{workout_id}").get_json()
    exercise = client.get(f"/exercises/{exercise_id}").get_json()

    assert workout["exercises"][0]["id"] == exercise_id
    assert workout["workout_exercises"][0]["sets"] == 3
    assert exercise["workouts"][0]["id"] == workout_id


@pytest.mark.parametrize("body", [
    {},
    {"reps": 10},
    {"duration_seconds": 0},
    {"reps": -1, "sets": 3},
])
def test_invalid_measurements(client, body):
    workout_id, exercise_id = create_pair(client)
    response = client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises",
        json=body,
    )
    assert response.status_code == 400


def test_timed_exercise(client):
    workout_id, exercise_id = create_pair(client)
    response = client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises",
        json={"duration_seconds": 60},
    )
    assert response.status_code == 201


def test_invalid_inputs(client):
    assert client.post("/workouts", json={
        "date": "invalid",
        "duration_minutes": 30,
    }).status_code == 400

    assert client.post("/workouts", json={
        "date": "2026-10-13",
        "duration_minutes": 0,
    }).status_code == 400

    assert client.post("/exercises", json={
        "name": " ",
        "category": "Strength",
        "equipment_needed": False,
    }).status_code == 400

    assert client.post("/exercises", json={}).status_code == 400
    assert client.post("/workouts", json=[]).status_code == 400
    assert client.post(
        "/workouts",
        data="{",
        content_type="application/json",
    ).status_code == 400


def test_missing_resources(client):
    for path in ("/workouts/999", "/exercises/999"):
        assert client.get(path).status_code == 404
        assert client.delete(path).status_code == 404

    assert client.post(
        "/workouts/999/exercises/999/workout_exercises",
        json={"duration_seconds": 60},
    ).status_code == 404


@pytest.mark.parametrize("parent", ["workouts", "exercises"])
def test_cascade_preserves_other_parent(client, parent):
    workout_id, exercise_id = create_pair(client)

    response = client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises",
        json={"reps": 10, "sets": 3},
    )
    assert response.status_code == 201

    parent_id = workout_id if parent == "workouts" else exercise_id
    response = client.delete(f"/{parent}/{parent_id}")

    assert response.status_code == 204
    assert response.data == b""

    with app.app_context():
        assert WorkoutExercise.query.count() == 0
        if parent == "workouts":
            assert Exercise.query.count() == 1
        else:
            assert Workout.query.count() == 1


def test_model_validation(client):
    with app.app_context():
        with pytest.raises(ValueError):
            Exercise(name=" ", category="Strength")

        with pytest.raises(ValueError):
            Workout(duration_minutes=-1)


def test_database_constraints(client):
    # Direct inserts bypass model validators and test the database itself.
    with app.app_context():
        with pytest.raises(IntegrityError):
            db.session.execute(
                db.insert(Exercise).values(
                    name=" ",
                    category="Strength",
                    equipment_needed=False,
                )
            )
            db.session.commit()
        db.session.rollback()

        with pytest.raises(IntegrityError):
            db.session.execute(
                db.insert(Workout).values(
                    date=__import__("datetime").date(2026, 10, 13),
                    duration_minutes=0,
                    notes="",
                )
            )
            db.session.commit()
        db.session.rollback()