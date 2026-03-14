"""Çalışma (Study) listesi ve detay endpoint'leri."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.study import Study
from app.models.patient import Patient
from app.models.nodule import Nodule
from app.models.report import Report

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


# ── Demo seed data ──
DEMO_PATIENTS = [
    {"name": "HASTA-A7F3", "age": 62, "sex": "M", "smoking": "eski sigara"},
    {"name": "HASTA-B2D1", "age": 55, "sex": "F", "smoking": "hiç"},
    {"name": "HASTA-C9E4", "age": 71, "sex": "M", "smoking": "aktif sigara"},
    {"name": "HASTA-D5A8", "age": 48, "sex": "F", "smoking": "hiç"},
    {"name": "HASTA-E1C6", "age": 67, "sex": "M", "smoking": "eski sigara"},
    {"name": "HASTA-F8B2", "age": 58, "sex": "F", "smoking": "aktif sigara"},
]

DEMO_STUDIES = [
    {
        "modality": "CR", "desc": "PA Akciğer Grafisi", "status": "completed",
        "rads": "2", "pipeline": "cxr", "patient_idx": 0,
        "report": {
            "rads": "2", "ensemble": 0.18,
            "summary": "Her iki akciğer alanı doğal havalanmaktadır. Kardiyotorasik oran normal sınırlarda. Kostofrenik sinüsler açık. Mediastinal yapılar doğal. Patolojik kitle veya infiltrasyon saptanmadı.",
            "recommendation": "Yıllık tarama kontrolü yeterli.",
            "cxr_rec": "Normal — yıllık tarama",
        },
    },
    {
        "modality": "CT", "desc": "Toraks BT — Düşük Doz", "status": "completed",
        "rads": "4A", "pipeline": "ct", "patient_idx": 1,
        "nodules": [
            {"loc": "Sağ üst lob — anterior segment", "size": 12.4, "vol": 998.0,
             "density": "part-solid", "morph": "lobulated", "mal": 0.72, "conf": 0.94, "nrads": "4A"},
            {"loc": "Sol alt lob — bazal segment", "size": 5.1, "vol": 69.4,
             "density": "ground-glass", "morph": "smooth", "mal": 0.15, "conf": 0.88, "nrads": "2"},
        ],
        "report": {
            "rads": "4A", "ensemble": 0.68,
            "summary": "Sağ üst lobda 12.4 mm part-solid nodül saptandı — Lung-RADS 4A. Sol alt lobda 5.1 mm buzlu cam nodül mevcut — Lung-RADS 2. 3 ay sonra DDBT kontrolü önerilir.",
            "recommendation": "3 ay sonra düşük doz BT kontrolü. Klinik korelasyon önerilir.",
            "cxr_rec": "BT yönlendirmesi gerekli — şüpheli bulgu",
        },
    },
    {
        "modality": "CR", "desc": "PA Akciğer Grafisi", "status": "completed",
        "rads": "3", "pipeline": "cxr", "patient_idx": 2,
        "report": {
            "rads": "3", "ensemble": 0.42,
            "summary": "Sol alt zonda düşük dansiteli opasite izlenmektedir. Muhtemelen benign karakterde olmakla birlikte BT ile değerlendirme önerilir.",
            "recommendation": "6 ay sonra DDBT kontrolü önerilir.",
            "cxr_rec": "Şüpheli opasite — BT önerilir",
        },
    },
    {
        "modality": "CR", "desc": "PA Akciğer Grafisi", "status": "uploaded",
        "rads": None, "pipeline": None, "patient_idx": 3,
    },
    {
        "modality": "CT", "desc": "Toraks BT — Düşük Doz", "status": "completed",
        "rads": "4B", "pipeline": "ct", "patient_idx": 4,
        "nodules": [
            {"loc": "Sağ alt lob — posterior bazal", "size": 22.8, "vol": 6208.0,
             "density": "solid", "morph": "spiculated", "mal": 0.91, "conf": 0.97, "nrads": "4B"},
            {"loc": "Sağ üst lob — apikal", "size": 8.3, "vol": 299.7,
             "density": "solid", "morph": "lobulated", "mal": 0.55, "conf": 0.91, "nrads": "4A"},
            {"loc": "Sol üst lob — lingula", "size": 4.2, "vol": 38.8,
             "density": "ground-glass", "morph": "smooth", "mal": 0.08, "conf": 0.85, "nrads": "2"},
        ],
        "report": {
            "rads": "4B", "ensemble": 0.88,
            "summary": "Sağ alt lobda 22.8 mm spiküle solid nodül — yüksek malignite şüphesi. Sağ üst lobda 8.3 mm solid nodül. Sol üst lobda 4.2 mm buzlu cam nodül. Biyopsi veya cerrahi konsültasyon önerilir.",
            "recommendation": "Biyopsi / PET-BT değerlendirmesi. Acil konsültasyon.",
            "cxr_rec": "Acil BT yönlendirmesi",
        },
    },
    {
        "modality": "CR", "desc": "PA Akciğer Grafisi", "status": "completed",
        "rads": "1", "pipeline": "cxr", "patient_idx": 5,
        "report": {
            "rads": "1", "ensemble": 0.05,
            "summary": "Her iki akciğer alanı temiz. Patolojik bulgu saptanmadı. Negatif tarama.",
            "recommendation": "Yıllık tarama yeterli.",
            "cxr_rec": "Negatif — normal tarama",
        },
    },
]


@router.post("/seed-demo")
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """Demo verileri oluştur — test/sunum amaçlı."""
    # Check if already seeded
    result = await db.execute(select(func.count(Study.id)))
    if result.scalar_one() > 0:
        return {"message": "Demo verisi zaten mevcut", "seeded": False}

    now = datetime.now(timezone.utc)
    created_patients = []

    # Create patients
    for i, p in enumerate(DEMO_PATIENTS):
        patient = Patient(
            id=str(uuid.uuid4()),
            anonymous_id=p["name"],
            age=p["age"],
            sex=p["sex"],
            smoking_status=p["smoking"],
            created_at=now - timedelta(days=30 - i * 3),
        )
        db.add(patient)
        created_patients.append(patient)

    await db.flush()

    study_count = 0
    nodule_count = 0
    report_count = 0

    # Create studies with nodules and reports
    for i, sd in enumerate(DEMO_STUDIES):
        patient = created_patients[sd["patient_idx"]]
        study_id = str(uuid.uuid4())
        study = Study(
            id=study_id,
            study_instance_uid=f"1.2.840.113619.{uuid.uuid4().int % 10**12}",
            patient_id=patient.id,
            modality=sd["modality"],
            study_date=now - timedelta(days=20 - i * 3),
            description=sd["desc"],
            status=sd["status"],
            pipeline_type=sd.get("pipeline"),
            overall_lung_rads=sd.get("rads"),
            quality_score=0.95 if sd["status"] == "completed" else None,
            series_count=1 if sd["modality"] == "CR" else 4,
            instance_count=1 if sd["modality"] == "CR" else 312,
            created_at=now - timedelta(days=20 - i * 3),
            completed_at=now - timedelta(days=19 - i * 3) if sd["status"] == "completed" else None,
        )
        db.add(study)
        study_count += 1

        # Add nodules
        for nd in sd.get("nodules", []):
            nodule = Nodule(
                id=str(uuid.uuid4()),
                study_id=study_id,
                location_description=nd["loc"],
                diameter_mm=nd["size"],
                volume_mm3=nd["vol"],
                density=nd["density"],
                morphology=nd["morph"],
                malignancy_score=nd["mal"],
                detection_confidence=nd["conf"],
                lung_rads_category=nd["nrads"],
            )
            db.add(nodule)
            nodule_count += 1

        # Add report
        rpt = sd.get("report")
        if rpt:
            report = Report(
                id=str(uuid.uuid4()),
                study_id=study_id,
                overall_lung_rads=rpt["rads"],
                cxr_ensemble_score=rpt.get("ensemble"),
                cxr_recommendation=rpt.get("cxr_rec"),
                summary_tr=rpt["summary"],
                recommendation_tr=rpt["recommendation"],
                total_processing_seconds=12.4 + i * 3.2,
                cxr_model_votes={"ark": True, "torchxray": rpt.get("ensemble", 0) > 0.3,
                                 "xraydar": rpt.get("ensemble", 0) > 0.4, "medrax": True},
            )
            db.add(report)
            report_count += 1

    await db.commit()

    return {
        "message": "Demo verisi oluşturuldu",
        "seeded": True,
        "patients": len(created_patients),
        "studies": study_count,
        "nodules": nodule_count,
        "reports": report_count,
    }
