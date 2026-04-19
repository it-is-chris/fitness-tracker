import pytest
from httpx import AsyncClient

from tests.conftest import SAMPLE_WORKOUT


@pytest.mark.asyncio
async def test_personal_records(client: AsyncClient, auth_headers: dict):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)

    response = await client.get("/api/stats/personal-records", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    bench = next(r for r in data if r["exercise"] == "Bench Press")
    assert bench["max_weight_kg"] == 80.0


@pytest.mark.asyncio
async def test_personal_records_filter_by_exercise(
    client: AsyncClient, auth_headers: dict
):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)

    response = await client.get(
        "/api/stats/personal-records",
        params={"exercise_name": "bench press"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["exercise"] == "Bench Press"
    assert data[0]["max_weight_kg"] == 80.0


@pytest.mark.asyncio
async def test_personal_records_empty(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/stats/personal-records", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_personal_records_updates_with_new_pr(
    client: AsyncClient, auth_headers: dict
):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)

    heavier_workout = {
        "title": "PR Day",
        "started_at": "2025-01-15T09:00:00Z",
        "exercises": [
            {
                "name": "Bench Press",
                "muscle_group": "Chest",
                "order": 1,
                "sets": [
                    {"set_number": 1, "reps": 1, "weight_kg": 100.0, "rpe": 10.0},
                ],
            }
        ],
    }
    await client.post("/api/workouts", json=heavier_workout, headers=auth_headers)

    response = await client.get(
        "/api/stats/personal-records",
        params={"exercise_name": "Bench Press"},
        headers=auth_headers,
    )
    data = response.json()
    assert data[0]["max_weight_kg"] == 100.0


@pytest.mark.asyncio
async def test_exercise_history(client: AsyncClient, auth_headers: dict):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)

    response = await client.get(
        "/api/stats/exercise-history",
        params={"exercise_name": "Bench Press"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["weight_kg"] == 60.0


@pytest.mark.asyncio
async def test_exercise_history_case_insensitive(
    client: AsyncClient, auth_headers: dict
):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)

    response = await client.get(
        "/api/stats/exercise-history",
        params={"exercise_name": "bench press"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_exercise_history_no_results(client: AsyncClient, auth_headers: dict):
    response = await client.get(
        "/api/stats/exercise-history",
        params={"exercise_name": "Unicorn Curls"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []
