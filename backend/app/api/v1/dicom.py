"""DICOM yükleme ve yönetim endpoint'leri."""

import hashlib
import logging
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.patient import Patient
from app.models.study import Study
from app.services.dicom_service import DicomService

logger = logging.getLogger(__name__)
router = APIRouter()


class DicomUploadResponse(BaseModel):
    study_uid: str
    series_count: int
    instance_count: int
    patient_id: str | None = None
    study_id: str | None = None
    message: str


@router.post("/upload", response_model=DicomUploadResponse)
async def upload_dicom(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """DICOM dosyası yükle — pydicom parse + Orthanc + DB."""
    if not file.filename or not file.filename.lower().endswith(".dcm"):
        raise HTTPException(
            status_code=400, detail="Sadece .dcm dosyaları kabul edilir"
        )

    content = await file.read()

    # 1. pydicom ile parse et
    import pydicom

    try:
        ds = pydicom.dcmread(BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geçersiz DICOM dosyası: {e}")

    study_uid = str(getattr(ds, "StudyInstanceUID", ""))
    patient_dcm_id = str(getattr(ds, "PatientID", "UNKNOWN"))
    modality = str(getattr(ds, "Modality", ""))
    study_description = str(getattr(ds, "StudyDescription", ""))
    slice_thickness = float(getattr(ds, "SliceThickness", 0) or 0)

    if not study_uid:
        raise HTTPException(
            status_code=400, detail="DICOM dosyasında StudyInstanceUID bulunamadı"
        )

    # 2. Orthanc'a yükle
    dicom_svc = DicomService()
    orthanc_result = await dicom_svc.upload_to_orthanc(content)
    if "error" in orthanc_result:
        logger.warning(f"Orthanc yükleme uyarısı: {orthanc_result}")

    # 3. Patient bul veya oluştur
    anonymous_id = "ANON-" + hashlib.sha256(patient_dcm_id.encode()).hexdigest()[:8]

    result = await db.execute(
        select(Patient).where(Patient.anonymous_id == anonymous_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        patient = Patient(
            anonymous_id=anonymous_id,
            age=_parse_age(str(getattr(ds, "PatientAge", ""))),
            sex=str(getattr(ds, "PatientSex", ""))[:1] or None,
        )
        db.add(patient)
        await db.flush()

    # 4. Study bul veya oluştur
    result = await db.execute(
        select(Study).where(Study.study_instance_uid == study_uid)
    )
    study = result.scalar_one_or_none()

    if not study:
        study = Study(
            study_instance_uid=study_uid,
            patient_id=patient.id,
            modality=modality,
            description=study_description or None,
            slice_thickness=slice_thickness or None,
            instance_count=1,
        )
        db.add(study)
    else:
        study.instance_count += 1

    await db.commit()

    return DicomUploadResponse(
        study_uid=study_uid,
        series_count=1,
        instance_count=study.instance_count,
        patient_id=patient.anonymous_id,
        study_id=study.id,
        message=f"DICOM başarıyla yüklendi: {file.filename}",
    )


@router.post("/upload-batch")
async def upload_dicom_batch(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Birden fazla DICOM dosyası yükle."""
    results = []
    errors = []

    for f in files:
        try:
            result = await upload_dicom(file=f, db=db)
            results.append({
                "filename": f.filename,
                "status": "success",
                "study_uid": result.study_uid,
            })
        except HTTPException as e:
            errors.append({"filename": f.filename, "error": e.detail})
        except Exception as e:
            errors.append({"filename": f.filename, "error": str(e)})

    return {
        "uploaded": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors if errors else None,
    }


def _parse_age(age_str: str) -> int | None:
    """DICOM PatientAge → integer (örn: '045Y' → 45)."""
    if not age_str:
        return None
    try:
        digits = "".join(c for c in age_str if c.isdigit())
        if digits:
            return int(digits)
    except (ValueError, TypeError):
        pass
    return None
