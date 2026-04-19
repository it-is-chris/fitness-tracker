from datetime import datetime

from pydantic import BaseModel


# --- ExerciseSet schemas ---


class ExerciseSetCreate(BaseModel):
    set_number: int
    reps: int | None = None
    weight_kg: float | None = None
    duration_seconds: int | None = None
    rpe: float | None = None


class ExerciseSetResponse(BaseModel):
    id: int
    set_number: int
    reps: int | None
    weight_kg: float | None
    duration_seconds: int | None
    rpe: float | None

    model_config = {"from_attributes": True}


# --- Exercise schemas ---


class ExerciseCreate(BaseModel):
    name: str
    muscle_group: str | None = None
    order: int = 0
    sets: list[ExerciseSetCreate] = []


class ExerciseResponse(BaseModel):
    id: int
    name: str
    muscle_group: str | None
    order: int
    sets: list[ExerciseSetResponse]

    model_config = {"from_attributes": True}


# --- Workout schemas ---


class WorkoutCreate(BaseModel):
    title: str
    notes: str | None = None
    duration_minutes: int | None = None
    started_at: datetime
    exercises: list[ExerciseCreate] = []


class WorkoutResponse(BaseModel):
    id: int
    title: str
    notes: str | None
    duration_minutes: int | None
    started_at: datetime
    created_at: datetime
    exercises: list[ExerciseResponse]

    model_config = {"from_attributes": True}


class WorkoutSummary(BaseModel):
    """Lighter response for list endpoints — no nested exercises."""

    id: int
    title: str
    notes: str | None
    duration_minutes: int | None
    started_at: datetime
    created_at: datetime
    exercise_count: int

    model_config = {"from_attributes": True}


# --- Stats schemas ---


class PersonalRecord(BaseModel):
    exercise: str
    max_weight_kg: float
    reps_at_pr: int | None


class ExerciseHistoryEntry(BaseModel):
    date: datetime
    workout_title: str
    set_number: int
    reps: int | None
    weight_kg: float | None
    duration_seconds: int | None
    rpe: float | None
