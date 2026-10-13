from datetime import date

from app import app
from models import db, Exercise, Workout, WorkoutExercise


def seed_database():
    with app.app_context():
        # Remove join records first to respect foreign keys.
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()

        squats = Exercise(
            name="Squats",
            category="Strength",
            equipment_needed=False,
        )
        pushups = Exercise(
            name="Push-ups",
            category="Strength",
            equipment_needed=False,
        )
        running = Exercise(
            name="Running",
            category="Cardio",
            equipment_needed=False,
        )

        strength = Workout(
            date=date(2026, 10, 12),
            duration_minutes=45,
            notes="Full-body strength session",
        )
        cardio = Workout(
            date=date(2026, 10, 13),
            duration_minutes=30,
            notes="Easy cardio session",
        )

        entries = [
            WorkoutExercise(
                workout=strength,
                exercise=squats,
                reps=12,
                sets=3,
            ),
            WorkoutExercise(
                workout=strength,
                exercise=pushups,
                reps=10,
                sets=3,
            ),
            WorkoutExercise(
                workout=cardio,
                exercise=running,
                duration_seconds=1200,
            ),
            WorkoutExercise(
                workout=cardio,
                exercise=squats,
                reps=10,
                sets=2,
            ),
        ]

        db.session.add_all(
            [squats, pushups, running, strength, cardio, *entries]
        )
        db.session.commit()

        print(
            f"Seeded {Exercise.query.count()} exercises, "
            f"{Workout.query.count()} workouts, "
            f"{WorkoutExercise.query.count()} workout entries."
        )


if __name__ == "__main__":
    seed_database()