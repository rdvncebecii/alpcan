"""Ajan 3 — Karakterizasyon: NB07 ResNet-50+CBAM + NB13 EfficientNet-B0+Tabular

NB07: suspicious AUC=0.977, 4-class risk
NB13: malignity AUC=0.991, 5-class Lung-RADS  ← birincil
Her nodül için 19 radiomic özellik hesaplanır, scaler NB13 training setinden.
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
    name = "Characterization (NB07+NB13)"
    version = "0.3.0"
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
            volume  = preprocessed.get("volume")
            if not nodules:
                return {"nodule_results": [], "total_nodules": 0}
            results = CharacterizationInference.predict_nodule_list(
                volume=volume,
                nodules=nodules,
            )
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

        lr_order = {"1": 0, "2": 1, "3": 2, "4A": 3, "4B": 4, "4X": 5}
        categories = [r.get("lung_rads", "1") for r in results]
        overall = max(categories, key=lambda x: lr_order.get(x, 0), default="1")

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
