"""Ajan 1 — Ön İşleme: SimpleITK 2.3 + pydicom 2.4

DICOM okuma, HU normalizasyon, akciğer maskesi, anonimleştirme.
GPU gerektirmez — CPU ile 30-60 s/tarama.
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class PreprocessAgent(BaseAgent):
    name = "Preprocessing"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """DICOM dizin yolunu kontrol et."""
        dicom_path = input_data.get("dicom_path")
        if not dicom_path:
            raise ValueError("dicom_path gerekli")
        return {"dicom_path": dicom_path}

    def predict(self, preprocessed: dict) -> dict:
        """Tam ön işleme pipeline'ı: DICOM → normalize 3D volume."""
        from ml.inference.ct_preprocess_inference import CTPreprocessInference

        if not CTPreprocessInference.is_loaded():
            CTPreprocessInference.load_model({
                "hu_min": -1000,
                "hu_max": 400,
                "target_spacing": [1.0, 1.0, 1.0],
                "lung_threshold_hu": -600,
            })

        return CTPreprocessInference.predict(preprocessed["dicom_path"])

    def postprocess(self, prediction: dict) -> dict:
        """Normalize 3D volume çıktısı."""
        return {
            "findings": {
                "volume_shape": list(prediction.get("resampled_shape", [])),
                "original_shape": list(prediction.get("original_shape", [])),
                "voxel_spacing": list(prediction.get("spacing", [])),
                "lung_mask_applied": prediction.get("lung_mask") is not None,
                "metadata": prediction.get("metadata", {}),
            },
            "confidence": 1.0,
            # Pipeline'a veri aktarımı için (numpy array — findings'e alınmaz)
            "volume": prediction.get("volume"),        # [0,1] normalize
            "volume_hu": prediction.get("volume_hu"),  # ham HU — nodül tespiti için
            "lung_mask": prediction.get("lung_mask"),
        }
