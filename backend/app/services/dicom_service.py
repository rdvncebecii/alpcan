"""DICOM Service — Orthanc entegrasyonu ve DICOM yönetimi."""

import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class DicomService:
    """Orthanc DICOM sunucusu ile iletişim."""

    def __init__(self):
        self.orthanc_url = settings.orthanc_url

    async def upload_to_orthanc(self, dicom_bytes: bytes) -> dict:
        """DICOM dosyasını Orthanc'a yükle."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.orthanc_url}/instances",
                content=dicom_bytes,
                headers={"Content-Type": "application/dicom"},
            )
            if response.status_code == 200:
                return response.json()
            logger.error(f"Orthanc upload failed: {response.status_code}")
            return {"error": response.text}

    async def get_studies(self) -> list[dict]:
        """Orthanc'taki tüm çalışmaları listele."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.orthanc_url}/studies")
            if response.status_code == 200:
                study_ids = response.json()
                studies = []
                for sid in study_ids:
                    detail = await client.get(f"{self.orthanc_url}/studies/{sid}")
                    if detail.status_code == 200:
                        studies.append(detail.json())
                return studies
            return []

    async def get_study(self, study_id: str) -> dict | None:
        """Belirli bir çalışmanın detayını getir."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.orthanc_url}/studies/{study_id}")
            if response.status_code == 200:
                return response.json()
            return None

    async def health_check(self) -> bool:
        """Orthanc bağlantısını kontrol et."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.orthanc_url}/system")
                return response.status_code == 200
        except Exception:
            return False
