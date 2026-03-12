from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

router = APIRouter()


class DicomUploadResponse(BaseModel):
    study_uid: str
    series_count: int
    instance_count: int
    patient_id: str | None = None
    message: str


@router.post("/upload", response_model=DicomUploadResponse)
async def upload_dicom(file: UploadFile = File(...)):
    """DICOM dosyası yükle ve Orthanc'a gönder."""
    if not file.filename or not file.filename.endswith(".dcm"):
        raise HTTPException(status_code=400, detail="Sadece .dcm dosyaları kabul edilir")

    # TODO: pydicom ile parse et, Orthanc'a forward et
    return DicomUploadResponse(
        study_uid="1.2.3.4.5.6.7.8.9.0",
        series_count=1,
        instance_count=1,
        patient_id="ANON-001",
        message="DICOM başarıyla yüklendi (stub)",
    )


@router.post("/upload-batch")
async def upload_dicom_batch(files: list[UploadFile] = File(...)):
    """Birden fazla DICOM dosyası yükle."""
    # TODO: Batch upload implementasyonu
    return {
        "uploaded": len(files),
        "message": f"{len(files)} dosya yüklendi (stub)",
    }
