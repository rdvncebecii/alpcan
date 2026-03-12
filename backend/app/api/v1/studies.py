from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class StudySummary(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    modality: str  # CT or CXR
    study_date: datetime
    description: str | None = None
    status: str  # pending, processing, completed, error
    nodule_count: int | None = None
    lung_rads: str | None = None


@router.get("/", response_model=list[StudySummary])
async def list_studies(
    modality: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """Çalışma listesini getir."""
    # TODO: Veritabanından çek
    return [
        StudySummary(
            id="study-001",
            patient_id="ANON-001",
            patient_name="Anonim Hasta",
            modality="CT",
            study_date=datetime.now(),
            description="Toraks BT",
            status="completed",
            nodule_count=2,
            lung_rads="3",
        )
    ]


@router.get("/{study_id}", response_model=StudySummary)
async def get_study(study_id: str):
    """Tek bir çalışmanın detayını getir."""
    # TODO: Veritabanından çek
    return StudySummary(
        id=study_id,
        patient_id="ANON-001",
        patient_name="Anonim Hasta",
        modality="CT",
        study_date=datetime.now(),
        description="Toraks BT",
        status="completed",
        nodule_count=2,
        lung_rads="3",
    )
