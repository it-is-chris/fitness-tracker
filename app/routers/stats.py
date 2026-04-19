from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.workout import Workout
from app.models.exercise import Exercise
from app.models.exercise_set import ExerciseSet
from app.schemas.workout import PersonalRecord, ExerciseHistoryEntry

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/personal-records", response_model=list[PersonalRecord])
async def get_personal_records(
    exercise_name: str | None = Query(None, description="Filter by exercise name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personal records (heaviest weight) per exercise."""
    max_weight_subq = (
        select(
            func.lower(Exercise.name).label("name_lower"),
            func.max(ExerciseSet.weight_kg).label("max_weight_kg"),
        )
        .join(ExerciseSet, ExerciseSet.exercise_id == Exercise.id)
        .join(Workout, Exercise.workout_id == Workout.id)
        .where(Workout.user_id == current_user.id, ExerciseSet.weight_kg.is_not(None))
        .group_by(func.lower(Exercise.name))
        .subquery()
    )

    query = (
        select(
            Exercise.name,
            max_weight_subq.c.max_weight_kg,
            func.max(ExerciseSet.reps).label("reps_at_pr"),
        )
        .join(Workout, Exercise.workout_id == Workout.id)
        .join(ExerciseSet, ExerciseSet.exercise_id == Exercise.id)
        .join(
            max_weight_subq,
            (func.lower(Exercise.name) == max_weight_subq.c.name_lower)
            & (ExerciseSet.weight_kg == max_weight_subq.c.max_weight_kg),
        )
        .where(Workout.user_id == current_user.id)
        .group_by(Exercise.name, max_weight_subq.c.max_weight_kg)
    )

    if exercise_name:
        query = query.where(func.lower(Exercise.name) == exercise_name.lower())

    result = await db.execute(query)
    rows = result.all()

    return [
        PersonalRecord(exercise=r.name, max_weight_kg=r.max_weight_kg, reps_at_pr=r.reps_at_pr)
        for r in rows
    ]


@router.get("/exercise-history", response_model=list[ExerciseHistoryEntry])
async def get_exercise_history(
    exercise_name: str,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get history of a specific exercise across all workouts."""
    result = await db.execute(
        select(
            Workout.started_at,
            Workout.title,
            ExerciseSet.set_number,
            ExerciseSet.reps,
            ExerciseSet.weight_kg,
            ExerciseSet.duration_seconds,
            ExerciseSet.rpe,
        )
        .join(Exercise, ExerciseSet.exercise_id == Exercise.id)
        .join(Workout, Exercise.workout_id == Workout.id)
        .where(
            Workout.user_id == current_user.id,
            func.lower(Exercise.name) == exercise_name.lower(),
        )
        .order_by(Workout.started_at.desc(), ExerciseSet.set_number)
        .limit(limit)
    )
    rows = result.all()

    return [
        ExerciseHistoryEntry(
            date=r.started_at,
            workout_title=r.title,
            set_number=r.set_number,
            reps=r.reps,
            weight_kg=r.weight_kg,
            duration_seconds=r.duration_seconds,
            rpe=r.rpe,
        )
        for r in rows
    ]
