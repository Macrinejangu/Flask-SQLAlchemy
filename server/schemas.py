from marshmallow import (
    Schema,
    ValidationError,
    fields,
    validate,
    validates_schema,
)


def not_blank(value):
    if not value.strip():
        raise ValidationError("Must not be blank.")


class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        validate=[validate.Length(min=1, max=100), not_blank],
    )
    category = fields.String(
        required=True,
        validate=[validate.Length(min=1, max=50), not_blank],
    )
    equipment_needed = fields.Boolean(required=True)

    @validates_schema
    def check_equipment_type(self, data, **kwargs):
        if type(data.get("equipment_needed")) is not bool:
            raise ValidationError(
                {"equipment_needed": ["Must be a boolean."]}
            )


class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(
        required=True,
        strict=True,
        validate=validate.Range(min=1),
    )
    notes = fields.String(load_default="")


class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(
        strict=True,
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=1),
    )
    sets = fields.Integer(
        strict=True,
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=1),
    )
    duration_seconds = fields.Integer(
        strict=True,
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=1),
    )

    @validates_schema
    def check_measurements(self, data, **kwargs):
        reps = data.get("reps")
        sets = data.get("sets")
        duration = data.get("duration_seconds")

        if (reps is None) != (sets is None):
            raise ValidationError(
                "Provide reps and sets together."
            )

        if reps is None and duration is None:
            raise ValidationError(
                "Provide reps and sets, or duration_seconds."
            )


class WorkoutEntrySchema(WorkoutExerciseSchema):
    exercise = fields.Nested(ExerciseSchema, dump_only=True)


class ExerciseEntrySchema(WorkoutExerciseSchema):
    workout = fields.Nested(WorkoutSchema, dump_only=True)


class WorkoutDetailSchema(WorkoutSchema):
    exercises = fields.Nested(
        ExerciseSchema,
        many=True,
        dump_only=True,
    )
    workout_exercises = fields.Nested(
        WorkoutEntrySchema,
        many=True,
        dump_only=True,
    )


class ExerciseDetailSchema(ExerciseSchema):
    workouts = fields.Nested(
        WorkoutSchema,
        many=True,
        dump_only=True,
    )
    workout_exercises = fields.Nested(
        ExerciseEntrySchema,
        many=True,
        dump_only=True,
    )