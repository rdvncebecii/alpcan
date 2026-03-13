"""Ajan 10 — CXR Kalite Kontrol: Heuristik tabanlı

Akciğer grafisi kalite değerlendirmesi.
PA pozisyon, netlik, rotasyon, artefakt kontrolü.
CPU ile <1 s/grafi.
"""

import logging
from pathlib import Path

import numpy as np

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class CXRQualityAgent(BaseAgent):
    name = "CXR Quality Control"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "cxr"

    def preprocess(self, input_data: dict) -> dict:
        """CXR görüntüsünü grayscale numpy array'e dönüştür."""
        from ml.preprocessing.cxr_transforms import load_cxr_from_dicom
        from PIL import Image

        image_path = input_data.get("image_path")
        if not image_path:
            raise ValueError("image_path gerekli")

        path = Path(image_path)
        if path.suffix.lower() == ".dcm":
            img_array = load_cxr_from_dicom(path)
        else:
            img = Image.open(path).convert("L")
            img_array = np.array(img)

        return {"image_array": img_array, "image_path": image_path}

    def predict(self, preprocessed: dict) -> dict:
        """Heuristik tabanlı kalite skorlama."""
        from ml.inference.cxr_quality_inference import CXRQualityInference

        if not CXRQualityInference.is_loaded():
            CXRQualityInference.load_model({
                "laplacian_threshold": 100.0,
                "min_image_size": 256,
                "min_dynamic_range": 50,
            })

        return CXRQualityInference.predict(preprocessed["image_array"])

    def postprocess(self, prediction: dict) -> dict:
        """Kalite kararı: GEÇTİ / UYARI / RED."""
        score = prediction.get("quality_score", 0)
        if score >= 80:
            decision = "GEÇTİ"
        elif score >= 50:
            decision = "UYARI"
        else:
            decision = "RED"

        return {
            "findings": {
                "quality_score": score,
                "decision": decision,
                "sharpness_ok": prediction.get("sharpness_ok"),
                "dynamic_range_ok": prediction.get("dynamic_range_ok"),
                "size_ok": prediction.get("size_ok"),
                "rotation_ok": prediction.get("rotation_ok"),
                "artifact_ok": prediction.get("artifact_ok"),
                "details": prediction.get("details", {}),
            },
            "confidence": score / 100.0,
        }
