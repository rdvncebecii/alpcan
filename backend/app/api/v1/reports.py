"""Rapor endpoint'leri — Lung-RADS raporları."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.study import Study

router = APIRouter()


class NoduleFinding(BaseModel):
    id: str
    location: str | None = None
    size_mm: float
    volume_mm3: float | None = None
    density: str | None = None
    lung_rads: str | None = None
    malignancy_score: float | None = None
    recommendation: str | None = None


class LungRADSReport(BaseModel):
    study_id: str
    patient_id: str
    report_date: datetime
    overall_lung_rads: str
    nodules: list[NoduleFinding] = []
    cxr_ensemble_score: float | None = None
    cxr_recommendation: str | None = None
    summary_tr: str | None = None
    recommendation_tr: str | None = None
    total_processing_seconds: float | None = None


@router.get("/{study_id}", response_model=LungRADSReport)
async def get_report(study_id: str, db: AsyncSession = Depends(get_db)):
    """Çalışma için Lung-RADS raporunu getir."""
    result = await db.execute(
        select(Study)
        .options(
            selectinload(Study.report),
            selectinload(Study.nodules),
            selectinload(Study.patient),
        )
        .where(Study.id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")

    if not study.report:
        raise HTTPException(
            status_code=404,
            detail="Rapor henüz oluşturulmadı. Önce analiz başlatın.",
        )

    report = study.report
    nodule_findings = [
        NoduleFinding(
            id=n.id,
            location=n.location_description,
            size_mm=n.diameter_mm,
            volume_mm3=n.volume_mm3,
            density=n.density,
            lung_rads=n.lung_rads_category,
            malignancy_score=n.malignancy_score,
        )
        for n in (study.nodules or [])
    ]

    return LungRADSReport(
        study_id=study.id,
        patient_id=study.patient_id,
        report_date=report.created_at,
        overall_lung_rads=report.overall_lung_rads,
        nodules=nodule_findings,
        cxr_ensemble_score=report.cxr_ensemble_score,
        cxr_recommendation=report.cxr_recommendation,
        summary_tr=report.summary_tr,
        recommendation_tr=report.recommendation_tr,
        total_processing_seconds=report.total_processing_seconds,
    )


@router.get("/{study_id}/pdf")
async def download_report_pdf(study_id: str, db: AsyncSession = Depends(get_db)):
    """Raporu PDF olarak indir."""
    result = await db.execute(
        select(Study).options(selectinload(Study.report)).where(Study.id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study or not study.report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı")

    if study.report.pdf_path:
        from fastapi.responses import FileResponse

        return FileResponse(study.report.pdf_path, media_type="application/pdf")

    return {
        "message": "PDF rapor oluşturma henüz implemente edilmedi",
        "study_id": study_id,
    }
