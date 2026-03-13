"""3D ResNet-50 + CBAM — nodül karakterizasyonu.

Model ağırlıkları Kaggle'da eğitim aşamasında.
Ağırlıklar hazır olduğunda:
- Input: 64×64×64 nodül patch
- Output: malignite skoru, yoğunluk, morfoloji, Lung-RADS

Bağımlılıklar: torch (gelecekte)
"""

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError


class CharacterizationInference(BaseInferenceModel):
    """3D ResNet-50 + CBAM nodül karakterizasyonu.

    Mevcut durum: ModelNotAvailableError — Kaggle eğitimi devam ediyor.

    Ağırlıklar hazır olduğunda:
    - Input: 64×64×64 patch (nodül merkezi etrafında)
    - Output: malignite skoru (0-1), yoğunluk, morfoloji, Lung-RADS, Grad-CAM
    """

    @classmethod
    def load_model(cls, config: dict) -> None:
        raise ModelNotAvailableError(
            "3D ResNet-50 + CBAM",
            "Kaggle eğitimi devam ediyor (notebook 03_resnet50_cbam). "
            "Ağırlıklar hazır olduğunda bu modül güncellenecek.",
        )

    @classmethod
    def predict(cls, patch: np.ndarray) -> dict:
        """Nodül karakterizasyonu.

        Args:
            patch: (64, 64, 64) veya (B, 1, 64, 64, 64) nodül patch

        Returns:
            {
                "malignancy_score": float (0-1),
                "density": str (solid/part-solid/ground-glass),
                "morphology": str (smooth/lobulated/spiculated/irregular),
                "lung_rads": str (1/2/3/4A/4B/4X),
                "gradcam": np.ndarray | None,
            }
        """
        raise ModelNotAvailableError(
            "3D ResNet-50 + CBAM",
            "Kaggle eğitimi devam ediyor.",
        )
