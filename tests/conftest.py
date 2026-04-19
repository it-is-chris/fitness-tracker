import os

# Override settings BEFORE any app imports so config.py reads these
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-not-for-production"

import pytest_asyncio  # noqa: E402
from app.config import settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

engine = create_async_engine(settings.database_url)
test_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Yield a test database session."""
    async with test_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Async test client with database dependency overridden."""

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
    """Register a test user and return auth headers with JWT token."""
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
