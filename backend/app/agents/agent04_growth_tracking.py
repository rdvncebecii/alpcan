"""Ajan 4 — Büyüme Takibi: Siamese 3D CNN + VoxelMorph v0.5

Volümetrik büyüme takibi + VDT (Volume Doubling Time) hesabı.
VDT <400 gün: yüksek malignite | >600 gün: muhtemelen benign.
Gelecek faz — not_available döner.
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class GrowthTrackingAgent(BaseAgent):
    name = "Growth Tracking (Siamese CNN)"
    version = "0.2.0"
    requires_gpu = True
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """Önceki çalışma kontrolü."""
        return {
            "has_previous_study": input_data.get("has_previous_study", False),
            "nodules": input_data.get("nodules", []),
        }

    def predict(self, preprocessed: dict) -> dict:
        """Siamese CNN ile büyüme analizi."""
        if not preprocessed.get("has_previous_study"):
            return {"growth_results": [], "status": "no_previous_study"}

        from ml.inference.growth_tracking_inference import GrowthTrackingInference
        from ml.inference.base import ModelNotAvailableError

        try:
            return GrowthTrackingInference.predict(None)
        except ModelNotAvailableError as e:
            logger.info(f"Büyüme takibi mevcut değil: {e}")
            return {"growth_results": [], "status": "not_available", "reason": str(e)}

    def postprocess(self, prediction: dict) -> dict:
        """VDT yorumları."""
        if prediction.get("status") in ("not_available", "no_previous_study"):
            return {
                "findings": {
                    "has_previous": False,
                    "growth_results": [],
                    "status": prediction.get("status"),
                    "reason": prediction.get("reason", "Önceki çalışma yok"),
                },
                "confidence": None,
            }

        results = prediction.get("growth_results", [])
        for r in results:
            vdt = r.get("vdt_days")
            if vdt and vdt < 400:
                r["vdt_interpretation"] = "Yüksek malignite riski"
            elif vdt and vdt < 600:
                r["vdt_interpretation"] = "Belirsiz — yakın takip"
            elif vdt:
                r["vdt_interpretation"] = "Büyük ihtimalle benign"

        return {
            "findings": {
                "has_previous": bool(results),
                "growth_results": results,
            },
            "confidence": None,
        }
