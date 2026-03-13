"""Ajan 2 — Nodül Tespit: nnU-Net v2.5.1 (3D ResEnc-L)

3D nodül segmentasyonu — tüm akciğer taranır.
Hedef: Duyarlılık >%90, FPR<0.5/tarama.
GPU: 1× A100 80GB, ~45-90 s/BT.
Ağırlıklar henüz eğitilmedi — not_available döner.
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class NoduleDetectionAgent(BaseAgent):
    name = "Nodule Detection (nnU-Net)"
    version = "0.2.0"
    requires_gpu = True
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """Pipeline'dan gelen volume ve mask'ı al."""
        return {
            "volume": input_data.get("volume"),
            "lung_mask": input_data.get("lung_mask"),
        }

    def predict(self, preprocessed: dict) -> dict:
        """nnU-Net ile 3D segmentasyon."""
        from ml.inference.nodule_detection_inference import NoduleDetectionInference
        from ml.inference.base import ModelNotAvailableError

        try:
            return NoduleDetectionInference.predict(
                volume=preprocessed.get("volume"),
                lung_mask=preprocessed.get("lung_mask"),
            )
        except ModelNotAvailableError as e:
            logger.info(f"nnU-Net mevcut değil: {e}")
            return {"nodules": [], "status": "not_available", "reason": str(e)}

    def postprocess(self, prediction: dict) -> dict:
        """Nodül listesi."""
        if prediction.get("status") == "not_available":
            return {
                "findings": {
                    "nodule_count": 0,
                    "nodules": [],
                    "status": "not_available",
                    "reason": prediction.get("reason", ""),
                },
                "confidence": None,
            }

        nodules = prediction.get("nodules", [])
        return {
            "findings": {
                "nodule_count": len(nodules),
                "nodules": nodules,
            },
            "confidence": max((n.get("confidence", 0) for n in nodules), default=0.0),
        }
