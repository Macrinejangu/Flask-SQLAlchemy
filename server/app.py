import os
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from models import db, Exercise, Workout, WorkoutExercise
from schemas import (
    ExerciseSchema,
    ExerciseDetailSchema,
    WorkoutSchema,
    WorkoutDetailSchema,
    WorkoutExerciseSchema,
)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, connection_record):
    if connection.__class__.__module__.startswith("sqlite3"):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///app.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)


def load_input(schema):
    data = request.get_json()

    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")

    return schema.load(data)


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    db.session.rollback()
    return jsonify({"errors": error.messages}), 400


@app.errorhandler(ValueError)
def handle_value_error(error):
    db.session.rollback()
    return jsonify({"error": str(error)}), 400


@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    db.session.rollback()
    return jsonify({"error": "Data violates a database constraint."}), 400


@app.errorhandler(BadRequest)
@app.errorhandler(UnsupportedMediaType)
def handle_invalid_json(error):
    return jsonify({"error": "Send valid JSON with Content-Type application/json."}), 400


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({"error": "Resource not found."}), 404


def get_workout(workout_id):
    return db.get_or_404(Workout, workout_id)


def get_exercise(exercise_id):
    return db.get_or_404(Exercise, exercise_id)


@app.route("/")
def home():
    return jsonify({"message": "Workout API"}), 200


@app.route("/workouts", methods=["GET"])
def list_workouts():
    workouts = db.session.execute(
        db.select(Workout).order_by(Workout.id)
    ).scalars().all()

    return jsonify(WorkoutSchema(many=True).dump(workouts)), 200


@app.route("/workouts/<int:workout_id>", methods=["GET"])
def show_workout(workout_id):
    workout = get_workout(workout_id)
    return jsonify(WorkoutDetailSchema().dump(workout)), 200


@app.route("/workouts", methods=["POST"])
def create_workout():
    data = load_input(WorkoutSchema())
    workout = Workout(**data)

    db.session.add(workout)
    db.session.commit()

    return jsonify(WorkoutSchema().dump(workout)), 201


@app.route("/workouts/<int:workout_id>", methods=["DELETE"])
def delete_workout(workout_id):
    workout = get_workout(workout_id)

    db.session.delete(workout)
    db.session.commit()

    return "", 204


@app.route("/exercises", methods=["GET"])
def list_exercises():
    exercises = db.session.execute(
        db.select(Exercise).order_by(Exercise.id)
    ).scalars().all()

    return jsonify(ExerciseSchema(many=True).dump(exercises)), 200


@app.route("/exercises/<int:exercise_id>", methods=["GET"])
def show_exercise(exercise_id):
    exercise = get_exercise(exercise_id)
    return jsonify(ExerciseDetailSchema().dump(exercise)), 200


@app.route("/exercises", methods=["POST"])
def create_exercise():
    data = load_input(ExerciseSchema())
    exercise = Exercise(**data)

    db.session.add(exercise)
    db.session.commit()

    return jsonify(ExerciseSchema().dump(exercise)), 201


@app.route("/exercises/<int:exercise_id>", methods=["DELETE"])
def delete_exercise(exercise_id):
    exercise = get_exercise(exercise_id)

    db.session.delete(exercise)
    db.session.commit()

    return "", 204


@app.route(
    "/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises",
    methods=["POST"],
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = get_workout(workout_id)
    exercise = get_exercise(exercise_id)
    data = load_input(WorkoutExerciseSchema())

    entry = WorkoutExercise(
        workout=workout,
        exercise=exercise,
        **data,
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify(WorkoutExerciseSchema().dump(entry)), 201


if __name__ == "__main__":
    app.run(port=5555, debug=True)