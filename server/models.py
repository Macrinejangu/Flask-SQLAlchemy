from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

db = SQLAlchemy()


def positive_integer(value, field):
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return value


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.CheckConstraint("length(trim(name)) > 0", name="exercise_name_not_blank"),
        db.CheckConstraint(
            "length(trim(category)) > 0",
            name="exercise_category_not_blank",
        ),
    )

    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )
    workouts = association_proxy("workout_exercises", "workout")

    @validates("name", "category")
    def validate_text(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        limit = 100 if key == "name" else 50
        if len(value.strip()) > limit:
            raise ValueError(f"{key} must be at most {limit} characters")
        return value.strip()

    @validates("equipment_needed")
    def validate_equipment(self, key, value):
        if type(value) is not bool:
            raise ValueError("equipment_needed must be a boolean")
        return value


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text, nullable=False, default="")

    __table_args__ = (
        db.CheckConstraint(
            "duration_minutes > 0",
            name="workout_duration_positive",
        ),
    )

    workout_exercises = db.relationship(
        "WorkoutExercise",
        back_populates="workout",
        cascade="all, delete-orphan",
    )
    exercises = association_proxy("workout_exercises", "exercise")

    @validates("date")
    def validate_date(self, key, value):
        if type(value) is not date:
            raise ValueError("date must be a Python date")
        return value

    @validates("duration_minutes")
    def validate_duration(self, key, value):
        return positive_integer(value, key)

    @validates("notes")
    def validate_notes(self, key, value):
        if not isinstance(value, str):
            raise ValueError("notes must be a string")
        return value


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey("workouts.id"),
        nullable=False,
    )
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercises.id"),
        nullable=False,
    )
    reps = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.CheckConstraint(
            "reps IS NULL OR reps > 0",
            name="workout_exercise_reps_positive",
        ),
        db.CheckConstraint(
            "sets IS NULL OR sets > 0",
            name="workout_exercise_sets_positive",
        ),
        db.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="workout_exercise_duration_positive",
        ),
    )

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_measurement(self, key, value):
        if value is None:
            return None
        return positive_integer(value, key)