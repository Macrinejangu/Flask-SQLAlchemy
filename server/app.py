from flask import Flask, jsonify
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine

from models import db, Exercise, Workout, WorkoutExercise


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, connection_record):
    # SQLite requires foreign-key enforcement on each connection.
    if connection.__class__.__module__.startswith("sqlite3"):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.route("/")
def home():
    return jsonify({"message": "Workout API"}), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)