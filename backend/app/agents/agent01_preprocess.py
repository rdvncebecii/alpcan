"""Ajan 1 — Ön İşleme: SimpleITK 2.3 + pydicom 2.4

DICOM okuma, HU normalizasyon, akciğer maskesi, anonimleştirme.
GPU gerektirmez — CPU ile 30-60 s/tarama.
"""

from app.agents.base import BaseAgent


class PreprocessAgent(BaseAgent):
    name = "Preprocessing"
    version = "0.1.0"
    requires_gpu = False
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """DICOM serisini oku ve dilim sırala."""
        # TODO: pydicom ile DICOM okuma
        # TODO: Instance Number / Z koordinatı bazında sıralama
        return {
            "dicom_path": input_data.get("dicom_path"),
            "slice_count": 0,
            "status": "stub",
        }

    def predict(self, preprocessed: dict) -> dict:
        """HU normalizasyon, izotropik resampling, akciğer maskesi."""
        # TODO: HU kırpma [-1000, 400]
        # TODO: İzotropik yeniden örnekleme → 1mm³
        # TODO: Eşik tabanlı akciğer maskesi (-600 HU)
        # TODO: Morfolojik kapanma + bağlı bileşen analizi
        return {
            "volume_shape": [512, 512, 300],
            "voxel_spacing": [1.0, 1.0, 1.0],
            "hu_range": [-1000, 400],
            "lung_mask_applied": True,
            "status": "stub",
        }

    def postprocess(self, prediction: dict) -> dict:
        """Normalize 3D volume çıktısı."""
        return {
            "findings": {
                "volume_shape": prediction.get("volume_shape"),
                "voxel_spacing": prediction.get("voxel_spacing"),
                "lung_mask_applied": prediction.get("lung_mask_applied"),
                "anonymized": True,
            },
            "confidence": 1.0,
        }
