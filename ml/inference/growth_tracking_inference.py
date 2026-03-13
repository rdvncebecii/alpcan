"""Siamese 3D CNN + VoxelMorph — büyüme takibi.

Gelecek faz implementasyonu.
Volümetrik büyüme takibi + VDT (Volume Doubling Time) hesabı.

Bağımlılıklar: torch, voxelmorph (gelecekte)
"""

import numpy as np

from ml.inference.base import BaseInferenceModel, ModelNotAvailableError


class GrowthTrackingInference(BaseInferenceModel):
    """Siamese 3D CNN + VoxelMorph büyüme takibi.

    Mevcut durum: ModelNotAvailableError — gelecek faz.

    İmplementasyon planı:
    - VoxelMorph ile T1-T2 registration
    - Siamese CNN ile nodül eşleştirme
    - Volümetrik karşılaştırma
    - VDT hesabı (<400 gün: yüksek risk, >600 gün: muhtemelen benign)
    """

    @classmethod
    def load_model(cls, config: dict) -> None:
        raise ModelNotAvailableError(
            "Siamese 3D CNN + VoxelMorph",
            "Gelecek faz implementasyonu. "
            "Notebook 04_siamese_growth ile geliştirilecek.",
        )

    @classmethod
    def predict(
        cls,
        current_patch: np.ndarray,
        previous_patch: np.ndarray | None = None,
        time_delta_days: int = 0,
    ) -> dict:
        """Büyüme analizi.

        Args:
            current_patch: Güncel nodül patch (64, 64, 64)
            previous_patch: Önceki nodül patch (opsiyonel)
            time_delta_days: İki tarama arası gün farkı

        Returns:
            {
                "has_previous": bool,
                "volume_change_percent": float,
                "vdt_days": float (Volume Doubling Time),
                "assessment": str (stable/growing/shrinking/high_risk),
            }
        """
        raise ModelNotAvailableError(
            "Siamese 3D CNN + VoxelMorph",
            "Gelecek faz implementasyonu.",
        )
