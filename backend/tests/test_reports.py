"""Reports endpoint tests."""

import uuid
from datetime import datetime, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def test_report_not_found(client: AsyncClient):
    res = await client.get("/api/v1/reports/nonexistent-id")
    assert res.status_code == 404


async def test_report_no_report_yet(client: AsyncClient, sample_study):
    res = await client.get(f"/api/v1/reports/{sample_study.id}")
    assert res.status_code == 404
    assert "henüz oluşturulmadı" in res.json()["detail"]


async def test_report_with_data(client: AsyncClient, sample_study, db_session: AsyncSession):
    from app.models.report import Report

    report = Report(
        id=str(uuid.uuid4()),
        study_id=sample_study.id,
        overall_lung_rads="3",
        summary_tr="Sağ üst lobda 8mm nodül saptandı.",
        recommendation_tr="6 ay sonra kontrol önerilir.",
        total_processing_seconds=12.5,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(report)
    await db_session.commit()

    res = await client.get(f"/api/v1/reports/{sample_study.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["overall_lung_rads"] == "3"
    assert data["summary_tr"] == "Sağ üst lobda 8mm nodül saptandı."
