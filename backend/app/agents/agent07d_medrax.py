"""Ajan 7D — MedRAX (University of Toronto, ICML 2025)

MedSAM2 + Maira-2 + SwinV2 + DenseNet-121.
İlk sürüm: MedSAM segmentasyon odaklı.
~3-4 s/grafi, 8 GB VRAM önerilir.
"""

import logging
from pathlib import Path

from app.agents.base import BaseAgent
from app.config import settings

logger = logging.getLogger(__name__)


class MedRAXAgent(BaseAgent):
    name = "MedRAX"
    version = "0.2.0"
    requires_gpu = True
    pipeline = "cxr"

    def preprocess(self, input_data: dict) -> dict:
        """CXR görüntüsünü MedSAM formatına hazırla."""
        from ml.preprocessing.cxr_transforms import load_cxr_for_medsam

        image_path = input_data.get("image_path")
        if not image_path:
            raise ValueError("image_path gerekli")

        pil_image = load_cxr_for_medsam(Path(image_path))
        return {"pil_image": pil_image, "image_path": image_path}

    def predict(self, preprocessed: dict) -> dict:
        """MedSAM segmentasyon inference."""
        from ml.inference.medsam_inference import MedSAMInference
        from ml.inference.base import ModelNotAvailableError

        try:
            if not MedSAMInference.is_loaded():
                MedSAMInference.load_model({
                    "hf_model_id": "flaviagiammarino/medsam-vit-base",
                    "device": settings.inference_device,
                })

            result = MedSAMInference.predict(preprocessed["pil_image"])

            # Segmentasyon maskesinden şüpheli bölge tespiti
            mask = result.get("mask")
            has_segmentation = mask is not None and mask.sum() > 0

            # Maske alanı oranı — anormal büyük/küçük bölge şüpheli olabilir
            if has_segmentation:
                mask_ratio = float(mask.sum()) / mask.size
                suspicious = mask_ratio < 0.3 or mask_ratio > 0.85
            else:
                suspicious = False

            return {
                "segmentation_mask": mask,
                "confidence": result.get("confidence", 0.0),
                "suspicious": suspicious,
                "mask_ratio": float(mask.sum() / mask.size) if has_segmentation else 0.0,
            }
        except ModelNotAvailableError as e:
            logger.warning(f"MedSAM mevcut değil: {e}")
            return {"status": "not_available", "reason": str(e)}
        except Exception as e:
            logger.error(f"MedSAM hatası: {e}")
            return {"status": "error", "reason": str(e)}

    def postprocess(self, prediction: dict) -> dict:
        """Segmentasyon sonuçlarını yapılandır."""
        if prediction.get("status") in ("not_available", "error"):
            return {
                "findings": {
                    "status": prediction.get("status"),
                    "reason": prediction.get("reason", ""),
                    "is_suspicious": False,
                    "has_segmentation": False,
                },
                "confidence": None,
            }

        has_mask = prediction.get("segmentation_mask") is not None
        return {
            "findings": {
                "is_suspicious": prediction.get("suspicious", False),
                "has_segmentation": has_mask,
                "mask_ratio": prediction.get("mask_ratio", 0.0),
                "segmentation_confidence": prediction.get("confidence", 0.0),
            },
            "confidence": prediction.get("confidence", 0.0),
        }
