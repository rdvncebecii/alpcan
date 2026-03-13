"""MedSAM ViT-Base — medikal görüntü segmentasyonu.

Notebook 04'ten alınan inference mantığı.
HuggingFace üzerinden otomatik indirilir.

Bağımlılıklar: torch, transformers, numpy, PIL
"""

import logging
from typing import Any

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError

logger = logging.getLogger(__name__)


class MedSAMInference(BaseInferenceModel):
    """MedSAM ViT-Base — SAM tabanlı medikal segmentasyon.

    - HuggingFace'ten otomatik indirilir
    - Bounding box destekli bölge segmentasyonu
    - Akciğer bölgesi tam segmentasyonu
    """

    _model: Any = None
    _processor: Any = None
    _device: str = "cpu"

    @classmethod
    def load_model(cls, config: dict) -> None:
        """MedSAM modelini HuggingFace'ten yükle.

        Args:
            config: {"hf_model_id": str, "device": str}
        """
        from transformers import SamModel, SamProcessor

        model_id = config.get("hf_model_id", "flaviagiammarino/medsam-vit-base")
        cls._device = config.get("device", "cpu")

        logger.info(f"MedSAM yükleniyor: {model_id}")
        cls._model = SamModel.from_pretrained(model_id)
        cls._processor = SamProcessor.from_pretrained(model_id)
        cls._model = cls._model.to(cls._device)
        cls._model.eval()

        logger.info(f"MedSAM yüklendi: device={cls._device}")

    @classmethod
    def predict(cls, image: "np.ndarray | PIL.Image.Image") -> dict:
        """Tam akciğer segmentasyonu — görüntünün tamamını kapsar.

        Args:
            image: RGB numpy array (H, W, 3) veya PIL Image

        Returns:
            {
                "mask": np.ndarray (H, W) binary maske,
                "confidence": float,
                "bbox_used": [x1, y1, x2, y2],
            }
        """
        from PIL import Image

        if not cls.is_loaded():
            cls.load_model({})

        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        w, h = image.size
        # Tam görüntü bbox
        bbox = [0, 0, w, h]
        return cls.segment_region(image, bbox)

    @classmethod
    def segment_region(
        cls, image: "np.ndarray | PIL.Image.Image", bbox: list[int]
    ) -> dict:
        """Bounding box destekli bölge segmentasyonu.

        Args:
            image: RGB numpy array (H, W, 3) veya PIL Image
            bbox: [x1, y1, x2, y2] bounding box

        Returns:
            {
                "mask": np.ndarray (H, W) binary maske,
                "confidence": float,
                "bbox_used": [x1, y1, x2, y2],
            }
        """
        import torch
        from PIL import Image

        if not cls.is_loaded():
            cls.load_model({})

        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        # SamProcessor ile girdi hazırla
        inputs = cls._processor(
            image,
            input_boxes=[[[bbox]]],
            return_tensors="pt",
        )
        inputs = {k: v.to(cls._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = cls._model(**inputs)

        # Maske ve skor çıkar
        masks = cls._processor.image_processor.post_process_masks(
            outputs.pred_masks.cpu(),
            inputs["original_sizes"].cpu(),
            inputs["reshaped_input_sizes"].cpu(),
        )

        mask = masks[0][0, 0].numpy()  # İlk maske
        confidence = float(outputs.iou_scores.cpu().numpy().flatten()[0])

        return {
            "mask": (mask > 0.5).astype(np.uint8),
            "confidence": confidence,
            "bbox_used": bbox,
        }

    @classmethod
    def segment_multiple(
        cls, image: "np.ndarray | PIL.Image.Image", bboxes: list[list[int]]
    ) -> list[dict]:
        """Birden fazla bölge için segmentasyon.

        Args:
            image: RGB görüntü
            bboxes: [[x1,y1,x2,y2], ...] bounding box listesi

        Returns:
            [{"mask": ..., "confidence": ..., "bbox_used": ...}, ...]
        """
        results = []
        for bbox in bboxes:
            result = cls.segment_region(image, bbox)
            results.append(result)
        return results
