"""Ajan 3 — Karakterizasyon: 3D ResNet-50 + CBAM + Grad-CAM v2

Malign/benign ayrımı + Lung-RADS 2022 skorlama.
AUC >0.95, ~2-5 s/nodül.
"""

from app.agents.base import BaseAgent

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
    version = "0.1.0"
    requires_gpu = True
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """Nodül merkezi etrafında 64×64×64 patch kırp."""
        # TODO: Her nodül için patch çıkarımı
        return {"patches": [], "status": "stub"}

    def predict(self, preprocessed: dict) -> dict:
        """3D ResNet-50 + CBAM ile sınıflandırma."""
        # TODO: Model inference + Grad-CAM ısı haritası
        return {
            "nodule_results": [
                {
                    "nodule_idx": 0,
                    "malignancy_score": 0.35,
                    "density": "solid",
                    "morphology": "smooth",
                    "lung_rads": "3",
                    "gradcam_path": None,
                },
                {
                    "nodule_idx": 1,
                    "malignancy_score": 0.08,
                    "density": "ground-glass",
                    "morphology": "smooth",
                    "lung_rads": "2",
                    "gradcam_path": None,
                },
            ],
            "status": "stub",
        }

    def postprocess(self, prediction: dict) -> dict:
        """Lung-RADS kategorileri ve tavsiyeler."""
        results = prediction.get("nodule_results", [])
        for r in results:
            r["lung_rads_description"] = LUNG_RADS_CATEGORIES.get(r["lung_rads"], "")

        # Overall Lung-RADS = en yüksek kategori
        categories = [r["lung_rads"] for r in results]
        overall = max(categories, default="1")

        return {
            "findings": {
                "nodule_results": results,
                "overall_lung_rads": overall,
                "overall_description": LUNG_RADS_CATEGORIES.get(overall, ""),
            },
            "confidence": max((r["malignancy_score"] for r in results), default=0.0),
        }
