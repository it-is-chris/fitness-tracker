import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    user_data = {
        "username": "duplicate",
        "email": "first@example.com",
        "password": "pass123",
    }
    await client.post("/api/auth/register", json=user_data)

    response = await client.post(
        "/api/auth/register",
        json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "pass123",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    user_data = {
        "username": "user1",
        "email": "same@example.com",
        "password": "pass123",
    }
    await client.post("/api/auth/register", json=user_data)

    response = await client.post(
        "/api/auth/register",
        json={
            "username": "user2",
            "email": "same@example.com",
            "password": "pass123",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "mypassword",
        },
    )

    response = await client.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "correct",
        },
    )

    response = await client.post(
        "/api/auth/login",
        json={"username": "wrongpass", "password": "incorrect"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "whatever"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_no_token(client: AsyncClient):
    response = await client.get("/api/workouts")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/workouts",
        headers={"Authorization": "Bearer totally.invalid.token"},
    )
    assert response.status_code == 401
