"""Ajan 4 — Büyüme Takibi: Siamese 3D CNN + VoxelMorph v0.5

Volümetrik büyüme takibi + VDT (Volume Doubling Time) hesabı.
VDT <400 gün: yüksek malignite | >600 gün: muhtemelen benign.
"""

from app.agents.base import BaseAgent


class GrowthTrackingAgent(BaseAgent):
    name = "Growth Tracking (Siamese CNN)"
    version = "0.1.0"
    requires_gpu = True
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """T1 ve T2 BT'den nodül patch çiftleri oluştur."""
        # TODO: Önceki çalışmayı bul, nodül eşleştirmesi yap
        return {
            "has_previous_study": False,
            "nodule_pairs": [],
            "status": "stub",
        }

    def predict(self, preprocessed: dict) -> dict:
        """Siamese CNN ile büyüme analizi."""
        if not preprocessed.get("has_previous_study"):
            return {"growth_results": [], "status": "no_previous_study"}

        # TODO: VoxelMorph registration + volümetrik karşılaştırma
        return {
            "growth_results": [
                {
                    "nodule_idx": 0,
                    "previous_diameter_mm": 6.5,
                    "current_diameter_mm": 8.2,
                    "volume_change_percent": 26.2,
                    "vdt_days": 380,
                    "assessment": "high_risk",
                }
            ],
            "status": "stub",
        }

    def postprocess(self, prediction: dict) -> dict:
        """VDT yorumları ve Fleischner tavsiyesi."""
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
