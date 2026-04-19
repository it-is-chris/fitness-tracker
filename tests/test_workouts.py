import pytest
from httpx import AsyncClient

from tests.conftest import SAMPLE_WORKOUT


@pytest.mark.asyncio
async def test_create_workout(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Monday Push Day"
    assert len(data["exercises"]) == 2
    assert data["exercises"][0]["name"] == "Bench Press"
    assert len(data["exercises"][0]["sets"]) == 3
    assert data["exercises"][0]["sets"][0]["weight_kg"] == 60.0


@pytest.mark.asyncio
async def test_create_workout_no_exercises(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/workouts",
        json={
            "title": "Rest Day Cardio",
            "started_at": "2025-01-14T07:00:00Z",
            "duration_minutes": 30,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Rest Day Cardio"
    assert data["exercises"] == []


@pytest.mark.asyncio
async def test_create_workout_unauthenticated(client: AsyncClient):
    response = await client.post("/api/workouts", json=SAMPLE_WORKOUT)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_workouts(client: AsyncClient, auth_headers: dict):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)
    await client.post(
        "/api/workouts",
        json={
            "title": "Tuesday Pull Day",
            "started_at": "2025-01-14T09:00:00Z",
            "exercises": [],
        },
        headers=auth_headers,
    )

    response = await client.get("/api/workouts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Tuesday Pull Day"
    assert data[1]["title"] == "Monday Push Day"


@pytest.mark.asyncio
async def test_list_workouts_has_exercise_count(
    client: AsyncClient, auth_headers: dict
):
    await client.post("/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers)

    response = await client.get("/api/workouts", headers=auth_headers)
    data = response.json()
    assert data[0]["exercise_count"] == 2


@pytest.mark.asyncio
async def test_list_workouts_pagination(client: AsyncClient, auth_headers: dict):
    for i in range(3):
        await client.post(
            "/api/workouts",
            json={
                "title": f"Workout {i}",
                "started_at": f"2025-01-{10+i}T09:00:00Z",
            },
            headers=auth_headers,
        )

    response = await client.get(
        "/api/workouts", params={"skip": 1, "limit": 1}, headers=auth_headers
    )
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Workout 1"


@pytest.mark.asyncio
async def test_get_workout(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers
    )
    workout_id = create_resp.json()["id"]

    response = await client.get(f"/api/workouts/{workout_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Monday Push Day"
    assert len(data["exercises"]) == 2


@pytest.mark.asyncio
async def test_get_workout_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/workouts/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_workout_belongs_to_other_user(
    client: AsyncClient, auth_headers: dict
):
    """Users should not be able to see other users' workouts."""
    create_resp = await client.post(
        "/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers
    )
    workout_id = create_resp.json()["id"]

    await client.post(
        "/api/auth/register",
        json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "otherpass",
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"username": "otheruser", "password": "otherpass"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.get(f"/api/workouts/{workout_id}", headers=other_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_workout(client: AsyncClient, auth_headers: dict):
    create_resp = await client.post(
        "/api/workouts", json=SAMPLE_WORKOUT, headers=auth_headers
    )
    workout_id = create_resp.json()["id"]

    response = await client.delete(f"/api/workouts/{workout_id}", headers=auth_headers)
    assert response.status_code == 204

    get_resp = await client.get(f"/api/workouts/{workout_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_workout_not_found(client: AsyncClient, auth_headers: dict):
    response = await client.delete("/api/workouts/99999", headers=auth_headers)
    assert response.status_code == 404
