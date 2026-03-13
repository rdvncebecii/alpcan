"""Çalışma (Study) listesi ve detay endpoint'leri."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.study import Study

router = APIRouter()


class StudySummary(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    modality: str
    study_date: datetime
    description: str | None = None
    status: str
    nodule_count: int | None = None
    lung_rads: str | None = None


@router.get("/", response_model=list[StudySummary])
async def list_studies(
    modality: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Çalışma listesini getir."""
    query = select(Study).options(
        selectinload(Study.patient), selectinload(Study.nodules)
    )

    if modality:
        query = query.where(Study.modality == modality)
    if status:
        query = query.where(Study.status == status)

    query = query.order_by(Study.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    studies = result.scalars().all()

    return [
        StudySummary(
            id=s.id,
            patient_id=s.patient_id,
            patient_name=s.patient.anonymous_id if s.patient else "Bilinmiyor",
            modality=s.modality,
            study_date=s.study_date or s.created_at,
            description=s.description,
            status=s.status,
            nodule_count=len(s.nodules) if s.nodules else None,
            lung_rads=s.overall_lung_rads,
        )
        for s in studies
    ]


@router.get("/count")
async def get_study_count(
    modality: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Çalışma sayısını getir."""
    query = select(func.count(Study.id))
    if modality:
        query = query.where(Study.modality == modality)
    if status:
        query = query.where(Study.status == status)

    result = await db.execute(query)
    count = result.scalar_one()
    return {"count": count}


@router.get("/{study_id}", response_model=StudySummary)
async def get_study(study_id: str, db: AsyncSession = Depends(get_db)):
    """Tek bir çalışmanın detayını getir."""
    result = await db.execute(
        select(Study)
        .options(selectinload(Study.patient), selectinload(Study.nodules))
        .where(Study.id == study_id)
    )
    study = result.scalar_one_or_none()

    if not study:
        raise HTTPException(status_code=404, detail="Çalışma bulunamadı")

    return StudySummary(
        id=study.id,
        patient_id=study.patient_id,
        patient_name=study.patient.anonymous_id if study.patient else "Bilinmiyor",
        modality=study.modality,
        study_date=study.study_date or study.created_at,
        description=study.description,
        status=study.status,
        nodule_count=len(study.nodules) if study.nodules else None,
        lung_rads=study.overall_lung_rads,
    )
