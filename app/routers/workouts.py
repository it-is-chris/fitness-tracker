import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.workout import Workout
from app.models.exercise import Exercise
from app.models.exercise_set import ExerciseSet
from app.schemas.workout import WorkoutCreate, WorkoutResponse, WorkoutSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout_in: WorkoutCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a workout with nested exercises and sets in one request."""
    workout = Workout(
        user_id=current_user.id,
        title=workout_in.title,
        notes=workout_in.notes,
        duration_minutes=workout_in.duration_minutes,
        started_at=workout_in.started_at,
    )
    db.add(workout)
    await db.flush()

    for ex_in in workout_in.exercises:
        exercise = Exercise(
            workout_id=workout.id,
            name=ex_in.name,
            muscle_group=ex_in.muscle_group,
            order=ex_in.order,
        )
        db.add(exercise)
        await db.flush()

        for set_in in ex_in.sets:
            exercise_set = ExerciseSet(
                exercise_id=exercise.id,
                set_number=set_in.set_number,
                reps=set_in.reps,
                weight_kg=set_in.weight_kg,
                duration_seconds=set_in.duration_seconds,
                rpe=set_in.rpe,
            )
            db.add(exercise_set)

    result = await db.execute(
        select(Workout)
        .where(Workout.id == workout.id)
        .options(selectinload(Workout.exercises).selectinload(Exercise.sets))
    )
    logger.info(
        "Workout created: id=%d user_id=%d exercises=%d",
        workout.id,
        current_user.id,
        len(workout_in.exercises),
    )
    return result.scalar_one()


@router.get("", response_model=list[WorkoutSummary])
async def list_workouts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workouts for the current user, most recent first."""
    result = await db.execute(
        select(
            Workout.id,
            Workout.title,
            Workout.notes,
            Workout.duration_minutes,
            Workout.started_at,
            Workout.created_at,
            func.count(Exercise.id).label("exercise_count"),
        )
        .outerjoin(Exercise)
        .where(Workout.user_id == current_user.id)
        .group_by(Workout.id)
        .order_by(Workout.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    return [
        WorkoutSummary(
            id=r.id,
            title=r.title,
            notes=r.notes,
            duration_minutes=r.duration_minutes,
            started_at=r.started_at,
            created_at=r.created_at,
            exercise_count=r.exercise_count,
        )
        for r in rows
    ]


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single workout with all exercises and sets."""
    result = await db.execute(
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == current_user.id)
        .options(selectinload(Workout.exercises).selectinload(Exercise.sets))
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )

    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a workout and all its exercises/sets."""
    result = await db.execute(
        select(Workout).where(
            Workout.id == workout_id, Workout.user_id == current_user.id
        )
    )
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found"
        )

    await db.delete(workout)
    logger.info("Workout deleted: id=%d user_id=%d", workout_id, current_user.id)
