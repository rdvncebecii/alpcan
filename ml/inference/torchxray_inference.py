"""TorchXRayVision DenseNet-121 — 18 patoloji tespiti.

Notebook 02'den (cell 11-15) birebir alınan inference mantığı.
Ağırlıklar torchxrayvision paketi tarafından otomatik indirilir.

Bağımlılıklar: torch, torchxrayvision, numpy
"""

import logging
from typing import Any

import numpy as np

from ml.inference.base import BaseInferenceModel

logger = logging.getLogger(__name__)


class TorchXRayInference(BaseInferenceModel):
    """TorchXRayVision DenseNet-121 — 18 patoloji tespiti.

    - 224x224 grayscale girdi
    - xrv.datasets.normalize ile [-1024, 1024] aralığına normalize
    - 18 patoloji için olasılık skoru çıktısı
    - Ağırlıklar pip paketi ile otomatik iner
    - CPU'da <2s/grafi
    """

    _model: Any = None
    _device: str = "cpu"
    _pathologies: list[str] = []

    @classmethod
    def load_model(cls, config: dict) -> None:
        """DenseNet-121 modelini yükle.

        Args:
            config: {"weights_name": str, "device": str}
                weights_name: "densenet121-res224-all" (varsayılan)
                device: "cpu" veya "cuda"
        """
        import torch
        import torchxrayvision as xrv

        weights_name = config.get("weights_name", "densenet121-res224-all")
        cls._device = config.get("device", "cpu")

        logger.info(f"TorchXRayVision yükleniyor: {weights_name}")
        cls._model = xrv.models.DenseNet(weights=weights_name)
        cls._model.eval()
        cls._model = cls._model.to(cls._device)
        cls._pathologies = list(cls._model.pathologies)

        logger.info(
            f"TorchXRayVision yüklendi: {len(cls._pathologies)} patoloji, "
            f"device={cls._device}"
        )

    @classmethod
    def predict(cls, image: np.ndarray | "torch.Tensor") -> dict:
        """DenseNet-121 ile 18 patoloji tespiti.

        Args:
            image: Önceden işlenmiş tensor (1, 1, 224, 224) veya
                   ham grayscale numpy array (H, W) [0-255 aralığında]

        Returns:
            {
                "predictions": {"Nodule": 0.72, "Mass": 0.15, ...},
                "pathologies": ["Atelectasis", "Consolidation", ...],
                "raw_scores": np.ndarray,
            }
        """
        import torch

        if not cls.is_loaded():
            cls.load_model({})

        # numpy array geldiyse tensor'a dönüştür
        if isinstance(image, np.ndarray):
            import torchxrayvision as xrv

            if image.ndim == 2:
                # Ham görüntü — normalize et
                if image.max() > 1.0:
                    image = xrv.datasets.normalize(image.astype(np.float32), 255)
                image = image[np.newaxis, np.newaxis, ...]  # (1, 1, H, W)
            elif image.ndim == 3:
                image = image[np.newaxis, ...]  # (1, C, H, W)

            image = torch.from_numpy(image).float()

        image = image.to(cls._device)

        with torch.no_grad():
            output = cls._model(image)

        scores = output.cpu().numpy().flatten()

        predictions = {}
        for i, pathology in enumerate(cls._pathologies):
            if i < len(scores):
                predictions[pathology] = round(float(scores[i]), 4)

        return {
            "predictions": predictions,
            "pathologies": cls._pathologies,
            "raw_scores": scores,
        }
