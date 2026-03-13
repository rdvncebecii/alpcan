"""Ajan 7A — Ark+ Foundation Model (Nature, 2025)

Swin-Large Transformer — 14 patoloji tespiti (NIH14 head).
Google CXR-FM'i geçen tek açık kaynak foundation model.
700.000+ röntgenden eğitilmiş. MIT lisans.
~2-3 s/grafi CPU, <1s GPU.
"""

import logging
from pathlib import Path

from app.agents.base import BaseAgent
from app.config import settings

logger = logging.getLogger(__name__)


class ArkAgent(BaseAgent):
    name = "Ark+ Foundation"
    version = "0.2.0"
    requires_gpu = False
    pipeline = "cxr"

    def preprocess(self, input_data: dict) -> dict:
        """CXR görüntüsünü 768×768 RGB'ye dönüştür, ImageNet normalize et."""
        from ml.preprocessing.cxr_transforms import load_cxr_for_ark

        image_path = input_data.get("image_path")
        if not image_path:
            raise ValueError("image_path gerekli")

        image_tensor = load_cxr_for_ark(Path(image_path), img_size=768)
        return {"image_tensor": image_tensor, "image_path": image_path}

    def predict(self, preprocessed: dict) -> dict:
        """Ark+ Swin-L inference — 14 patoloji (NIH14 head)."""
        from ml.inference.ark_inference import ArkInference
        from ml.inference.base import ModelNotAvailableError

        try:
            if not ArkInference.is_loaded():
                ArkInference.load_model({
                    "weights_path": str(
                        Path(settings.model_weights_dir)
                        / "Ark6_swinLarge768_ep50.pth.tar"
                    ),
                    "device": settings.inference_device,
                    "checkpoint_key": "teacher",
                    "num_classes_list": [14, 14, 14, 3, 6, 1],
                    "projector_features": 1376,
                    "use_mlp": False,
                    "img_size": 768,
                    "patch_size": 4,
                    "window_size": 12,
                    "embed_dim": 192,
                    "depths": [2, 2, 18, 2],
                    "num_heads": [6, 12, 24, 48],
                    "head_n": 2,
                })

            return ArkInference.predict(preprocessed["image_tensor"])
        except ModelNotAvailableError as e:
            logger.warning(f"Ark+ mevcut değil: {e}")
            return {"predictions": {}, "status": "not_available", "reason": str(e)}

    def postprocess(self, prediction: dict) -> dict:
        """Şüpheli patoloji listesi."""
        if prediction.get("status") == "not_available":
            return {
                "findings": {
                    "status": "not_available",
                    "reason": prediction.get("reason", ""),
                },
                "confidence": None,
            }

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
