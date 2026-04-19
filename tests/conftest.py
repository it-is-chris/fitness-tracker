import asyncio
import atexit
import os

from sqlalchemy.engine.url import make_url
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

# --- Bootstrap: start a Postgres container and create the schema BEFORE any
# app imports, so Pydantic settings read the correct DATABASE_URL. ---

_postgres = PostgresContainer("postgres:16").start()
atexit.register(_postgres.stop)

_async_url = (
    make_url(_postgres.get_connection_url())
    .set(drivername="postgresql+asyncpg")
    .render_as_string(hide_password=False)
)

os.environ["DATABASE_URL"] = _async_url
os.environ["SECRET_KEY"] = "test-secret-not-for-production"

# --- Now safe to import app modules. ---

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# NullPool means each engine.connect() opens a fresh asyncpg connection,
# so we don't reuse connections across function-scoped event loops.
engine = create_async_engine(_async_url, poolclass=NullPool)


async def _create_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(_create_schema())


@pytest_asyncio.fixture
async def db():
    """Per-test DB session wrapped in a transaction that gets rolled back.

    `join_transaction_mode="create_savepoint"` turns any `session.commit()`
    inside the app into a SAVEPOINT release instead of a real commit, so the
    outer transaction is still live at test end and `rollback()` wipes
    everything cleanly — without the cost of recreating tables per test.
    """
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Async test client with the DB dependency overridden to share our
    transaction-bound session."""

    async def override_get_db():
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register a test user and return auth headers with a JWT token."""
    await client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
        },
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


SAMPLE_WORKOUT = {
    "title": "Monday Push Day",
    "notes": "Feeling strong today",
    "duration_minutes": 65,
    "started_at": "2025-01-13T09:00:00Z",
    "exercises": [
        {
            "name": "Bench Press",
            "muscle_group": "Chest",
            "order": 1,
            "sets": [
                {"set_number": 1, "reps": 10, "weight_kg": 60.0, "rpe": 7.0},
                {"set_number": 2, "reps": 8, "weight_kg": 70.0, "rpe": 8.0},
                {"set_number": 3, "reps": 6, "weight_kg": 80.0, "rpe": 9.0},
            ],
        },
        {
            "name": "Overhead Press",
            "muscle_group": "Shoulders",
            "order": 2,
            "sets": [
                {"set_number": 1, "reps": 10, "weight_kg": 30.0},
                {"set_number": 2, "reps": 8, "weight_kg": 35.0},
            ],
        },
    ],
}
