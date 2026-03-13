"""Ajan 7B — TorchXRayVision DenseNet-121

18 patoloji tespiti — nodül/kitle odaklı.
MIT lisans, PyTorch tek satır.
<2 s/grafi.
"""

import logging
from pathlib import Path

from app.agents.base import BaseAgent
from app.config import settings

logger = logging.getLogger(__name__)


class TorchXRayAgent(BaseAgent):
    name = "TorchXRayVision"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "cxr"

    def preprocess(self, input_data: dict) -> dict:
        """CXR görüntüsünü TorchXRayVision formatına dönüştür."""
        from ml.preprocessing.cxr_transforms import load_cxr_for_xrv

        image_path = input_data.get("image_path")
        if not image_path:
            raise ValueError("image_path gerekli")

        image_tensor = load_cxr_for_xrv(Path(image_path))
        return {"image_tensor": image_tensor, "image_path": image_path}

    def predict(self, preprocessed: dict) -> dict:
        """DenseNet-121 inference — 18 patoloji."""
        from ml.inference.torchxray_inference import TorchXRayInference

        if not TorchXRayInference.is_loaded():
            TorchXRayInference.load_model({
                "weights_name": "densenet121-res224-all",
                "device": settings.inference_device,
            })

        return TorchXRayInference.predict(preprocessed["image_tensor"])

    def postprocess(self, prediction: dict) -> dict:
        """Şüpheli bulgu listesi."""
        preds = prediction.get("predictions", {})
        threshold = 0.5
        suspicious = {k: v for k, v in preds.items() if v > threshold}
        return {
            "findings": {
                "all_predictions": preds,
                "suspicious_findings": suspicious,
                "is_suspicious": len(suspicious) > 0,
            },
            "confidence": max(preds.values(), default=0.0),
        }
