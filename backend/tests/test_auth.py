import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@papermind.io",
        "password": "StrongPassword123!",
        "full_name": "New User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@papermind.io"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient, test_user_a: dict):
    response = await client.post("/api/v1/auth/register", json={
        "email": test_user_a["email"],
        "password": "Password123!",
        "full_name": "Duplicate"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient, test_user_a: dict):
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user_a["email"],
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_bad_credentials(client: AsyncClient, test_user_a: dict):
    response = await client.post("/api/v1/auth/login", json={
        "email": test_user_a["email"],
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user_a: dict):
    response = await client.get("/api/v1/auth/me", headers=test_user_a["headers"])
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_a["email"]
