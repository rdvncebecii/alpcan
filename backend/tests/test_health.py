"""Health endpoint tests."""

from httpx import AsyncClient


async def test_health(client: AsyncClient):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "alpcan-api"


async def test_root(client: AsyncClient):
    res = await client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "AlpCAN API"
    assert data["status"] == "running"
