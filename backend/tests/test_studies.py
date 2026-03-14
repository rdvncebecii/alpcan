"""Studies endpoint tests."""

from httpx import AsyncClient


async def test_list_studies_empty(client: AsyncClient):
    res = await client.get("/api/v1/studies/")
    assert res.status_code == 200
    assert res.json() == []


async def test_list_studies_with_data(client: AsyncClient, sample_study):
    res = await client.get("/api/v1/studies/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_study.id
    assert data[0]["modality"] == "CR"
    assert data[0]["status"] == "uploaded"


async def test_get_study(client: AsyncClient, sample_study):
    res = await client.get(f"/api/v1/studies/{sample_study.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == sample_study.id


async def test_get_study_not_found(client: AsyncClient):
    res = await client.get("/api/v1/studies/nonexistent-id")
    assert res.status_code == 404


async def test_study_count(client: AsyncClient, sample_study):
    res = await client.get("/api/v1/studies/count")
    assert res.status_code == 200
    assert res.json()["count"] == 1


async def test_study_filter_modality(client: AsyncClient, sample_study):
    res = await client.get("/api/v1/studies/?modality=CT")
    assert res.status_code == 200
    assert len(res.json()) == 0

    res = await client.get("/api/v1/studies/?modality=CR")
    assert res.status_code == 200
    assert len(res.json()) == 1
