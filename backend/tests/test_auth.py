"""Authentication endpoint tests."""

from httpx import AsyncClient


async def test_register(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dr@alpcan.net",
            "full_name": "Dr. Test",
            "password": "securepass123",
            "role": "radiologist",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "dr@alpcan.net"
    assert data["role"] == "radiologist"
    assert "id" in data


async def test_register_duplicate(client: AsyncClient):
    payload = {
        "email": "dr@alpcan.net",
        "full_name": "Dr. Test",
        "password": "securepass123",
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201

    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409


async def test_login(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dr@alpcan.net",
            "full_name": "Dr. Test",
            "password": "securepass123",
        },
    )

    # Login
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "dr@alpcan.net", "password": "securepass123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dr@alpcan.net",
            "full_name": "Dr. Test",
            "password": "securepass123",
        },
    )

    res = await client.post(
        "/api/v1/auth/login",
        data={"username": "dr@alpcan.net", "password": "wrongpass"},
    )
    assert res.status_code == 401


async def test_me(client: AsyncClient):
    # Register + Login
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dr@alpcan.net",
            "full_name": "Dr. Test",
            "password": "securepass123",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "dr@alpcan.net", "password": "securepass123"},
    )
    token = login_res.json()["access_token"]

    # Get me
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "dr@alpcan.net"


async def test_me_no_token(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
