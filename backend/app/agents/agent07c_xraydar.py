"""Ajan 7C — X-Raydar (Lancet Digital Health, 2023)

ResNet-50 + Transformer hybrid — 37 bulgu tespiti.
Radyologu %13.3 geride bırakır.
Model kodu herkese açık değil — ModelNotAvailableError döner.
"""

import logging

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class XRaydarAgent(BaseAgent):
    name = "X-Raydar"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "cxr"

    def preprocess(self, input_data: dict) -> dict:
        """CXR görüntü yolunu aktar."""
        return {"image_path": input_data.get("image_path")}

    def predict(self, preprocessed: dict) -> dict:
        """X-Raydar inference — model kodu mevcut değil."""
        from ml.inference.xraydar_inference import XRaydarInference
        from ml.inference.base import ModelNotAvailableError

        try:
            return XRaydarInference.predict(None)
        except ModelNotAvailableError as e:
            logger.info(f"X-Raydar mevcut değil: {e}")
            return {"predictions": {}, "status": "not_available", "reason": str(e)}

    def postprocess(self, prediction: dict) -> dict:
        """Model mevcut değilse zarif sonuç döndür."""
        if prediction.get("status") == "not_available":
            return {
                "findings": {
                    "status": "not_available",
                    "reason": prediction.get("reason", ""),
                    "is_suspicious": False,
                },
                "confidence": None,
            }

        preds = prediction.get("predictions", {})
        suspicious = {k: v for k, v in preds.items() if v > 0.5}
        return {
            "findings": {
                "all_predictions": preds,
                "suspicious_findings": suspicious,
                "is_suspicious": len(suspicious) > 0,
            },
            "confidence": max(preds.values(), default=0.0),
        }
