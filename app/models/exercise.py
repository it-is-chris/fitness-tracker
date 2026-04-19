from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    muscle_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    workout: Mapped["Workout"] = relationship(back_populates="exercises")  # noqa: F821
    sets: Mapped[list["ExerciseSet"]] = relationship(  # noqa: F821
        back_populates="exercise", cascade="all, delete-orphan"
    )
