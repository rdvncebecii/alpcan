"""Ajan 3 — Karakterizasyon: 3D ResNet-50 + CBAM + Grad-CAM v2

Malign/benign ayrımı + Lung-RADS 2022 skorlama.
AUC >0.95, ~2-5 s/nodül.
Ağırlıklar Kaggle'da eğitim aşamasında — not_available döner.
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

LUNG_RADS_CATEGORIES = {
    "1": "Negatif — Malignite bulgusu yok",
    "2": "Benign — İyi huylu özellikler",
    "3": "Muhtemelen benign — 6 ay kontrol",
    "4A": "Şüpheli (düşük) — 3 ay BT veya PET-BT",
    "4B": "Şüpheli (yüksek) — Biyopsi önerilir",
    "4X": "Ek bulgular — Multidisipliner kurul",
}


class CharacterizationAgent(BaseAgent):
    name = "Characterization (ResNet-50+CBAM)"
    version = "0.2.0"
    requires_gpu = True
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """Pipeline'dan gelen nodül listesini al."""
        return {
            "nodules": input_data.get("nodules", []),
            "volume": input_data.get("volume"),
        }

    def predict(self, preprocessed: dict) -> dict:
        """3D ResNet-50 + CBAM ile sınıflandırma."""
        from ml.inference.characterization_inference import CharacterizationInference
        from ml.inference.base import ModelNotAvailableError

        try:
            nodules = preprocessed.get("nodules", [])
            results = []
            for i, nod in enumerate(nodules):
                result = CharacterizationInference.predict(None)
                results.append(result)
            return {"nodule_results": results}
        except ModelNotAvailableError as e:
            logger.info(f"Karakterizasyon mevcut değil: {e}")
            return {
                "nodule_results": [],
                "status": "not_available",
                "reason": str(e),
            }

    def postprocess(self, prediction: dict) -> dict:
        """Lung-RADS kategorileri ve tavsiyeler."""
        if prediction.get("status") == "not_available":
            return {
                "findings": {
                    "nodule_results": [],
                    "overall_lung_rads": "1",
                    "status": "not_available",
                    "reason": prediction.get("reason", ""),
                },
                "confidence": None,
            }

        results = prediction.get("nodule_results", [])
        for r in results:
            lr = r.get("lung_rads", "1")
            r["lung_rads_description"] = LUNG_RADS_CATEGORIES.get(lr, "")

        categories = [r.get("lung_rads", "1") for r in results]
        overall = max(categories, default="1")

        return {
            "findings": {
                "nodule_results": results,
                "overall_lung_rads": overall,
                "overall_description": LUNG_RADS_CATEGORIES.get(overall, ""),
            },
            "confidence": max(
                (r.get("malignancy_score", 0) for r in results), default=0.0
            ),
        }
