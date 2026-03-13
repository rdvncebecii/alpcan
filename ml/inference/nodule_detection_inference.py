"""nnU-Net v2 — 3D nodül segmentasyonu.

Model ağırlıkları henüz LIDC-IDRI üzerinde eğitilmedi.
Ağırlıklar hazır olduğunda:
- Sliding window inference
- 5-fold ensemble
- Connected component analizi ile bireysel nodül çıkarımı

Bağımlılıklar: torch, nnunetv2 (gelecekte)
"""

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError


class NoduleDetectionInference(BaseInferenceModel):
    """nnU-Net v2 3D nodül segmentasyonu.

    Mevcut durum: ModelNotAvailableError — ağırlıklar henüz eğitilmedi.

    Ağırlıklar hazır olduğunda bu sınıf güncellenecek:
    - Input: (D, H, W) normalize 3D volume + lung mask
    - Output: Nodül listesi (merkez, çap, hacim, güven skoru, maske)
    """

    @classmethod
    def load_model(cls, config: dict) -> None:
        raise ModelNotAvailableError(
            "nnU-Net v2",
            "LIDC-IDRI üzerinde eğitim henüz tamamlanmadı. "
            "Kaggle notebook 02_nnunet_training ile eğitim yapılacak.",
        )

    @classmethod
    def predict(
        cls, volume: np.ndarray, lung_mask: np.ndarray | None = None
    ) -> dict:
        """3D nodül segmentasyonu.

        Args:
            volume: (D, H, W) normalize 3D volume
            lung_mask: (D, H, W) binary akciğer maskesi (opsiyonel)

        Returns:
            {
                "nodules": [{
                    "center": [x, y, z],
                    "diameter_mm": float,
                    "volume_mm3": float,
                    "confidence": float,
                    "segmentation_mask": np.ndarray (nodül bölgesi),
                }, ...],
                "total_nodules": int,
            }
        """
        raise ModelNotAvailableError(
            "nnU-Net v2",
            "LIDC-IDRI üzerinde eğitim henüz tamamlanmadı.",
        )
