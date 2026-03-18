"""Ajan 2 — Nodül Tespit: NB06 U-Net 2D (ResNet-34 encoder)

2D slice-by-slice CT nodül segmentasyonu.
Model: smp.Unet(resnet34), LIDC-IDRI, Dice=0.623, IoU=0.572
Gelecek: nnU-Net 3D (NB11 tamamlandığında)
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class NoduleDetectionAgent(BaseAgent):
    name = "Nodule Detection (U-Net 2D)"
    version = "0.3.0"
    requires_gpu = True
    pipeline = "ct"

    def preprocess(self, input_data: dict) -> dict:
        """Pipeline'dan gelen volume ve mask'ı al."""
        # volume_hu: ham HU değerleri (NoduleDetectionInference kendi pencerelemeyi yapar)
        # volume_hu yoksa eski volume'e fallback (geriye dönük uyumluluk)
        return {
            "volume": input_data.get("volume_hu") or input_data.get("volume"),
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
