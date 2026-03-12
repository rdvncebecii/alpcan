from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class NoduleFinding(BaseModel):
    id: int
    location: str
    size_mm: float
    volume_mm3: float | None = None
    density: str  # solid, part-solid, ground-glass
    lung_rads: str
    malignancy_score: float
    recommendation: str


class LungRADSReport(BaseModel):
    study_id: str
    patient_id: str
    report_date: datetime
    overall_lung_rads: str
    nodules: list[NoduleFinding]
    cxr_ensemble_score: float | None = None
    cxr_recommendation: str | None = None
    summary_tr: str  # Türkçe özet
    recommendation_tr: str  # Türkçe tavsiye


@router.get("/{study_id}", response_model=LungRADSReport)
async def get_report(study_id: str):
    """Çalışma için Lung-RADS raporunu getir."""
    # TODO: Veritabanından çek
    return LungRADSReport(
        study_id=study_id,
        patient_id="ANON-001",
        report_date=datetime.now(),
        overall_lung_rads="3",
        nodules=[
            NoduleFinding(
                id=1,
                location="Sağ üst lob, posterior segment",
                size_mm=8.2,
                volume_mm3=288.5,
                density="solid",
                lung_rads="3",
                malignancy_score=0.35,
                recommendation="6 ay sonra kontrol BT önerilir",
            ),
            NoduleFinding(
                id=2,
                location="Sol alt lob, bazal segment",
                size_mm=4.1,
                volume_mm3=36.1,
                density="ground-glass",
                lung_rads="2",
                malignancy_score=0.08,
                recommendation="Yıllık DDBT taraması",
            ),
        ],
        summary_tr="Sağ üst lobda 8.2 mm solid nodül — Lung-RADS 3. Sol alt lobda 4.1 mm buzlu cam nodül — Lung-RADS 2.",
        recommendation_tr="6 ay sonra kontrol BT önerilir. Yıllık DDBT taraması devam etmelidir.",
    )


@router.get("/{study_id}/pdf")
async def download_report_pdf(study_id: str):
    """Raporu PDF olarak indir."""
    # TODO: PDF oluşturma (Llama-3 ile)
    return {"message": "PDF rapor oluşturma henüz implemente edilmedi", "study_id": study_id}
